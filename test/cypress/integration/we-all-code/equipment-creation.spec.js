import faker from "faker";

const uuid = `${faker.datatype.number(9)}${faker.datatype.number(
  9
)}${faker.datatype.number(9)}-${faker.datatype.number(
  9
)}${faker.datatype.number(9)}${faker.datatype.number(
  9
)}-${faker.datatype.number(9)}${faker.datatype.number(
  9
)}${faker.datatype.number(9)}-${faker.datatype.number(
  9
)}${faker.datatype.number(9)}${faker.datatype.number(9)}`;
const equipment_type = faker.datatype.number({ min: 1, max: 2 });
const make = faker.commerce.productName();
const model = faker.datatype.number(20);
const tag = `${make}${model}`;
const notes = faker.lorem.words(5);
const acquisition_datetime = faker.date.between("2021-01-01", "2023-12-31");
const acquisition_date = acquisition_datetime.toLocaleDateString();
const acquisition_time = acquisition_datetime.toLocaleTimeString();

describe("Add an equipmentL required fields", () => {
  it("Creates equipment", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();
    cy.get("#user-tools > strong").should("have.text", "Ali");

    cy.get(".model-equipment > :nth-child(2) > .addlink").click();
    cy.get("#id_uuid").clear();
    cy.get("#id_uuid").type(uuid);
    cy.get("#id_equipment_type").select(`${equipment_type}`);
    cy.get("#id_make").clear();
    cy.get("#id_make").type(make);
    cy.get("#id_model").clear();
    cy.get("#id_model").type(model);
    cy.get("#id_asset_tag").clear();
    cy.get("#id_asset_tag").type(tag);
    cy.get("#id_condition").select("working");
    cy.get(".default").click();
    cy.get(".success").should("exist");
  });
});

describe("Add an equipment: complete", () => {
  it("Creates equipment with all fields", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();
    cy.get("#user-tools > strong").should("have.text", "Ali");

    cy.get(".model-equipment > :nth-child(2) > .addlink").click();
    cy.get("#id_uuid").clear();
    cy.get("#id_uuid").type(uuid);
    cy.get("#id_equipment_type").select(`${equipment_type}`);
    cy.get("#id_make").clear();
    cy.get("#id_make").type(make);
    cy.get("#id_model").clear();
    cy.get("#id_model").type(model);
    cy.get("#id_asset_tag").clear();
    cy.get("#id_asset_tag").type(tag);
    cy.get("#id_acquisition_date_0").type(acquisition_date);
    cy.get("#id_acquisition_date_1").type(acquisition_time.substring(0, acquisition_time.length - 3));
    cy.get("#id_condition").select("working");
    cy.get("#id_notes").type(notes);
    cy.get(".vCheckboxLabel").click();
    cy.get("#id_force_update_on_next_boot").check();
    cy.get(".default").click();
    cy.get(".success").should("exist");
  });
});
