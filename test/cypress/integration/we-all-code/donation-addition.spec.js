import faker from "faker";

const first_name = faker.name.firstName();
const last_name = faker.name.lastName();
const email = faker.internet.exampleEmail(first_name, last_name);
const referral_code = `e${faker.datatype.number({
  min: 1000,
  max: 99999,
})}`;
const donation = faker.datatype.number(10000);

// describe("Add a donation: required only", () => {
//   it("Creates donation", () => {
//     cy.visit("/dj-admin");
//     cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
//     cy.get("#id_password").type("admin");
//     cy.contains("Log in").click();
//     cy.get("#user-tools > strong").should("have.text", "Ali");

//     cy.get(".model-donation > :nth-child(2) > .addlink").click();
//     cy.get("#id_amount").type(donation);
//     cy.contains('Save').click();
//     cy.get('.success').should('exist');
//   });
// });

describe("Add a donation: complete", () => {
  it("Creates donation with all fields", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();
    cy.get("#user-tools > strong").should("have.text", "Ali");

    cy.get(".model-donation > :nth-child(2) > .addlink").click();
    cy.get(
      ".field-user > :nth-child(1) > .related-widget-wrapper > .select2 > .selection > .select2-selection"
    )
      .click()
      .wait(3000);
    cy.get(
      ".select2-container > .select2-dropdown > .select2-results > ul:first-child"
    ).click();
    cy.get(
      ".field-session > :nth-child(1) > .related-widget-wrapper > .select2 > .selection > .select2-selection"
    )
      .click()
      .wait(5000);
    cy.get(
      ".select2-container > .select2-dropdown > .select2-results > ul:first-child"
    )
      .click();

    cy.get("#id_first_name").clear();
    cy.get("#id_first_name").type(first_name);
    cy.get(".field-first_name").click();
    cy.get("#id_last_name").type(last_name);
    cy.get("#id_referral_code").type(referral_code);
    cy.get("#id_email").type(email);
    cy.get("#id_amount").type(donation);
    cy.get(".field-is_verified").click();
    cy.get(".field-is_verified > .checkbox-row > .vCheckboxLabel").click();
    cy.get("#id_is_verified").check();
    cy.get(".field-receipt_sent > .checkbox-row > .vCheckboxLabel").click();
    cy.get("#id_receipt_sent").check();
    cy.get(".default").click();
  });
});
