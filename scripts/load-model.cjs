// Local orchestration adapter. Service facts belong to each repository's YAML.
const fs = require("node:fs");
const path = require("node:path");
const yaml = require("../backstage/node_modules/js-yaml");
const root = path.resolve(__dirname, "..");
module.exports = require("./services.json").map((name) => {
  const entities = yaml.loadAll(
    fs.readFileSync(
      path.join(root, "services", name, "catalog-info.yaml"),
      "utf8"
    )
  );
  const component = entities.find((entity) => entity.kind === "Component");
  const annotations = component.metadata.annotations;
  return {
    name: component.metadata.name,
    port: Number(annotations["acmesecure.example/http-port"]),
    owner: component.spec.owner.split("/").pop(),
    route: annotations["acmesecure.example/http-route"],
    dependencies: component.spec.dependsOn.map((ref) => ref.split("/").pop()),
  };
});
if (require.main === module)
  process.stdout.write(JSON.stringify(module.exports));
