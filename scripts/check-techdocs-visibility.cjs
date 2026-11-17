// Exercise the same entity-predicate evaluator used by Backstage's entity tabs.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { test } = require("node:test");
const yaml = require("../backstage/node_modules/js-yaml");
const {
  filterPredicateToFilterFunction,
} = require("../backstage/node_modules/@backstage/filter-predicates");

const root = path.resolve(__dirname, "..");
const config = yaml.load(
  fs.readFileSync(path.join(root, "backstage/app-config.yaml"), "utf8")
);
const extension = config.app.extensions.find(
  (item) => item["entity-content:techdocs"]
);
const predicate = extension?.["entity-content:techdocs"]?.config?.filter;
// An entity content extension without a filter is visible for every entity.
const visible = predicate
  ? filterPredicateToFilterFunction(predicate)
  : () => true;
const org = yaml.loadAll(
  fs.readFileSync(path.join(root, "catalog/org.yaml"), "utf8")
);

test("Customer Experience does not open TechDocs Missing Annotation", () => {
  const team = org.find(
    (entity) =>
      entity.kind === "Group" && entity.metadata.name === "customer-experience"
  );
  assert.equal(
    visible(team),
    false,
    "TechDocs tab is visible for Customer Experience despite having no documentation source"
  );
});

test("undocumented organization, team, user, and system entities hide the tab", () => {
  const platform = yaml.loadAll(
    fs.readFileSync(path.join(root, "catalog/platform.yaml"), "utf8")
  );
  for (const entity of [...org, ...platform]) {
    assert.equal(
      visible(entity),
      false,
      `${entity.kind}:${entity.metadata.name} has no TechDocs`
    );
  }
});

test("all six domain-owned service documentation tabs stay visible", () => {
  for (const name of require("./services.json")) {
    const entity = yaml
      .loadAll(
        fs.readFileSync(
          path.join(root, "services", name, "catalog-info.yaml"),
          "utf8"
        )
      )
      .find((item) => item.kind === "Component");
    assert.equal(visible(entity), true, `${name} must retain its TechDocs tab`);
  }
});

test("an explicitly documented group or shared-docs reference can opt in", () => {
  for (const annotations of [
    { "backstage.io/techdocs-ref": "dir:." },
    { "backstage.io/techdocs-entity": "component:default/onboarding-service" },
  ]) {
    assert.equal(
      visible({
        apiVersion: "backstage.io/v1alpha1",
        kind: "Group",
        metadata: { name: "documented-team", annotations },
        spec: { type: "team", children: [] },
      }),
      true
    );
  }
});

test("customer-facing website documentation stays visible", () => {
  const entity = yaml.load(
    fs.readFileSync(path.join(root, "frontend/customer-portal/catalog-info.yaml"), "utf8")
  );
  assert.equal(visible(entity), true);
});
