"""Batch cadence [S37] and revenue types [S36]."""

JOB_CADENCE = {
    "cancellation_curves": "Saturdays",
    "booking_curves": "Nightly (except Saturdays)",
    "seasonality_factor": "Fridays",
    "deseasonalized_demand": "Nightly (except Saturdays)",
    "reference_prices": "Nightly (except Saturdays)",
    "mrm": "Monthly (not run since November 2010; March 2012 update rolled back)",
}

# Active BR5 revenue types [S36]. Trade revenue types are included in
# inventory but excluded from revenue [S36].
BR5_REVENUE_TYPES_LOCAL = [
    "Local Agency-Endorsement",
    "Local Agency-Natl Platform",
    "Local Agency-Political",
    "Local Agency-Sales",
    "Local Agency-Sales Incentive",
    "Local Direct-Endorsement",
    "Local Direct-Natl Platform",
    "Local Direct-Political",
    "Local Direct-Sales Incentive",
    "Local-Direct",
    "New Bus Local-Agency",
    "New Bus Local-Direct",
    "Preacher - CA mkts only",
    "Preacher-Local Agency",
]

BR5_REVENUE_TYPES_NATIONAL = [
    "LOCAL ENTERPRISE CCRS",
    "National Agency-Endorsement",
    "National Agency-Political",
    "National Agency-Sales",
    "National Direct-Political",
    "National-Direct Sales",
    "National-Natl Platform",
    "New Bus National Direct-Sales",
    "New Bus National-Agency",
    "Preacher-Natl Agency",
]
