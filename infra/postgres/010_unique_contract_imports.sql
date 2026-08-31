CREATE UNIQUE INDEX IF NOT EXISTS uq_xfollow_contracts_source
  ON xfollow.contracts(tenant_id, source_kind, source_id)
  WHERE source_id IS NOT NULL;

INSERT INTO xfollow.schema_migrations(version)
VALUES ('010_unique_contract_imports')
ON CONFLICT (version) DO NOTHING;
