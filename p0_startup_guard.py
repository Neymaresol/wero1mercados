"""Fail-closed policy for startup schema and catalog bootstrap."""


def startup_bootstrap_enabled(*, deployment_env: str, allow_mutations: str, mode: str) -> bool:
    """Allow startup DDL/seeders only in explicitly opted-in staging.

    Production, default deployments, and deployments without the explicit
    mutation opt-in must never create schema objects or seed offers at startup.
    """
    return (
        deployment_env.strip().casefold() == "staging"
        and allow_mutations.strip().casefold() in {"1", "true", "yes"}
        and mode.strip().casefold() != "production"
    )
