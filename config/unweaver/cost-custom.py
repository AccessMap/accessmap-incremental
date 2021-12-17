"""Defines cost function generators for optimal path finding."""
from datetime import datetime
import math
import humanized_opening_hours as hoh
import pytz

# Default base moving speeds for different modes. All in m/s.
# Slightly lower than average walking speed
WALK_BASE = 1.3
# Rough estimate
WHEELCHAIR_BASE = 0.6
# Roughly 5 mph
POWERED_BASE = 2

# 1 / DIVISOR = speed where cutoff starts to apply, dictates exponential"s k.
DIVISOR = 5

# "fastest" incline. -0.0087 is straight from Tobler"s hiking function
INCLINE_IDEAL = -0.0087

STREET_TYPES = [
    "secondary",
    "tertiary",
    "residential",
    "service",
]


def find_k(g, m, n):
    return math.log(n) / abs(g - m)


def tobler(grade, k=3.5, m=INCLINE_IDEAL, base=WALK_BASE):
    # Modified to be in meters / second rather than km / h
    return base * math.exp(-k * abs(grade - m))


def cost_fun_generator(
    base_speed=WALK_BASE,
    downhill=0.1,
    uphill=0.085,
    avoidCurbs=False,
    timestamp=None,
    streetAvoidance=1,
):
    """Calculates a cost-to-travel that balances distance vs. steepness vs.
    needing to cross the street.

    :param downhill: Maximum downhill incline indicated by the user, e.g.
                     0.1 for 10% downhill.
    :type downhill: float
    :param uphill: Positive incline (uphill) maximum, as grade.
    :type uphill: float
    :param avoidCurbs: Whether curb ramps should be avoided.
    :type avoidCurbs: bool

    """
    k_down = find_k(-downhill, INCLINE_IDEAL, DIVISOR)
    k_up = find_k(uphill, INCLINE_IDEAL, DIVISOR)

    if timestamp is None:
        date = datetime.now(pytz.timezone("US/Pacific"))
    else:
        # Unix epoch time is sent in integer format, but is in milliseconds.
        # Divide by 1000 to get seconds.
        date = datetime.fromtimestamp(
            timestamp / 1000, pytz.timezone("US/Pacific")
        )

    def cost_fun(u, v, d):
        """Cost function that evaluates every edge, returning either a
        nonnegative cost or None. Returning a value of None implies an infinite
        cost, i.e. that edge will be excluded from any paths.

        :param u: incoming node ID
        :type u: int
        :param v: ougoing node ID
        :type v: int
        :param d: The edge to evaluate.
        :type d: dict
        :returns: Cost of traversing the edge
        :rtype: float or None

        """
        time = 0
        speed = base_speed
        street_cost_factor = 1

        length = d["length"]
        highway = d["highway"]

        if highway == "footway":
            if "footway" in d:
                if d["footway"] == "crossing":
                    if avoidCurbs:
                        if "curbramps" in d:
                            if not d["curbramps"]:
                                return None
                        else:
                            # TODO: Make this user-configurable - we assume no
                            # curb ramps by default now
                            return None
                    # Add delay for crossing street
                    # TODO: tune this based on street type crossed and/or
                    # markings.
                    time += 30
                elif d.get("elevator", False):
                    opening_hours = d["opening_hours"]
                    # Add delay for using the elevator
                    time += 45
                    # See if the elevator has limited hours
                    try:
                        oh = hoh.OHParser(opening_hours)
                        if not oh.is_open(date):
                            return None
                    except KeyError:
                        # 'opening_hours' isn't on this elevator path
                        pass
                    except ValueError:
                        # 'opening_hours' is None (better option for checking?)
                        pass
                    except Exception:
                        # Something else went wrong. TODO: give a useful
                        # message back?
                        return None
                else:
                    # Handle all other footways the same

                    # FIXME: this data should be float to begin with
                    if "incline" in d:
                        incline = float(d["incline"])

                        # Decrease speed based on incline
                        if length > 3:
                            # If the path is very short, ignore incline due to
                            # likelihood that it is incorrectly estimated.
                            if (incline > uphill) or (incline < -downhill):
                                return None
                        if incline > INCLINE_IDEAL:
                            speed = tobler(
                                incline,
                                k=k_up,
                                m=INCLINE_IDEAL,
                                base=base_speed,
                            )
                        else:
                            speed = tobler(
                                incline,
                                k=k_down,
                                m=INCLINE_IDEAL,
                                base=base_speed,
                            )
        elif highway in STREET_TYPES:
            if highway == "pedestrian":
                # Pedestrian streets are good, use them with no extra cost
                # (Using 'abs' to ensure non-negative)
                street_cost_factor = abs(streetAvoidance + 1)
                pass
            elif highway == "service":
                # 10% extra cost for using a service road (includes alleys and
                # driveways and parking lots)
                street_cost_factor = 1.1 * (streetAvoidance + 1)
            elif highway == "residential":
                # It's a residential street and hopefully somewhat accessible.
                # Apply a 20% street cost
                street_cost_factor = 1.2 * (streetAvoidance + 1)
            else:
                # Apply an extra 50% cost for all other roads, which should
                # be considered potentially unsafe/unreliable due to higher
                # car traffic volume.
                street_cost_factor = 1.5 * (streetAvoidance + 1)
        else:
            # Unknown path type: do not use
            return None

        # Initial time estimate (in seconds) - based on speed
        time += length / speed

        cost = street_cost_factor * time

        return cost

    return cost_fun