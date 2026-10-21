# Hotmart intent funnel — isolated simulation
Version date: 2026-10-21 (America/Sao_Paulo)

This module is a pure, offline simulation. It NEVER calls Hotmart, posts campaigns, creates real clicks, writes a database, or initiates bank transfers.
Production integration is blocked until HotLink ownership, offer authorization, event provenance, isolated CI, staging Double Check and rollback are verified.

INT.1: a real campaign landing event, from a trusted server-side event collector.
INT.2: a real offer-detail interaction, from a trusted server-side event collector.
Neither client-supplied intent flags nor zero scores qualify. No event is proof of purchase.
Hotmart purchases and commissions require authenticated provider confirmation.
