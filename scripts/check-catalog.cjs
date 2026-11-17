// Validate source entities with the installed Backstage schemas, before ingestion.
const fs = require("node:fs");
const path = require("node:path");
const yaml = require("../backstage/node_modules/js-yaml");
const model = require("../backstage/node_modules/@backstage/catalog-model");
const root = path.resolve(__dirname, "..");
const manifest = require("./load-model.cjs");
async function main() {
  const entities = [];
  const files = [
    "catalog/all.yaml",
    "catalog/org.yaml",
    "catalog/platform.yaml",
    "frontend/customer-portal/catalog-info.yaml",
    ...manifest.map((s) => `services/${s.name}/catalog-info.yaml`),
  ];
  for (const file of files) {
    for (const entity of yaml.loadAll(
      fs.readFileSync(path.join(root, file), "utf8")
    )) {
      if (entity.kind === "API") {
        const contract = path.join(root, path.dirname(file), "openapi.yaml");
        if (entity.spec.definition !== fs.readFileSync(contract, "utf8"))
          throw new Error(
            `Stale embedded API: run python3 tools/sync-api.py inside ${path.dirname(
              contract
            )}`
          );
        const schema = yaml.load(entity.spec.definition);
        if (schema.openapi !== "3.1.0" || !schema.paths)
          throw new Error(`Invalid OpenAPI: ${contract}`);
        // Each repository compares the entire schema to FastAPI's generated OpenAPI.
      }
      model.entityEnvelopeSchemaValidator()(entity);
      const validator =
        model[entity.kind.toLowerCase() + "EntityV1alpha1Validator"];
      if (validator && !(await validator.check(entity)))
        throw new Error(`Invalid entity ${file}: ${entity.metadata.name}`);
      entities.push(entity);
    }
  }
  const refs = new Set(entities.map(model.stringifyEntityRef));
  for (const entity of entities) {
    for (const ref of [
      entity.spec.owner,
      entity.spec.system && `system:default/${entity.spec.system}`,
      entity.spec.domain && `domain:default/${entity.spec.domain}`,
      ...(entity.spec.dependsOn || []),
      ...(entity.spec.providesApis || []).map((a) => `api:default/${a}`),
      ...(entity.spec.consumesApis || []).map((a) => `api:default/${a}`),
    ].filter(Boolean)) {
      if (!refs.has(ref))
        throw new Error(`Unresolved ${ref} in ${entity.metadata.name}`);
    }
  }
  console.log(
    `Validated ${entities.length} source entities, six OpenAPI definitions, and all service references.`
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
