CAGE4_SUBNETS = (
    "restricted_zone_a_subnet",
    "operational_zone_a_subnet",
    "restricted_zone_b_subnet",
    "operational_zone_b_subnet",
    "public_access_zone_subnet"
)

ACTION_OBS_RESULTS = (
    "TRUE",             # The action was successful
    "UNKNOWN",          # It is not possible to know the success of the action / the action does not support 'success' types
    "FALSE",            # The action was unsuccessful
    "IN_PROGRESS"       # The action takes multiple steps and has not been completed yet.
)