import faker from "faker";

const additional_info = faker.lorem.words(5);
const start_datetime = faker.date.between("2021-01-01", "2023-12-31");
const end_datetime = new Date(start_datetime.getTime() + (60 * 60 * 1000));

console.log(start_datetime)

console.log(end_datetime)

const start_date = start_datetime.toLocaleDateString();
const start_time = start_datetime.toLocaleTimeString();
const end_date = end_datetime.toLocaleDateString();
const end_time = end_datetime.toLocaleTimeString();
const announced_datetime = new Date (start_datetime.getDate() - 6)
const announced_date = announced_datetime.toLocaleDateString();
const announced_time = announced_datetime.toLocaleTimeString();
const ext_enroll = `${faker.internet.url()}.example`;

it("Creates meeting: required fields", () => {
  cy.visit("/dj-admin");
  cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
  cy.get("#id_password").type("admin");
  cy.contains("Log in").click();
  cy.get("#user-tools > strong").should("have.text", "Ali");

  cy.get(".model-meeting > :nth-child(2) > .addlink").click();
  cy.get(
    ".field-meeting_type > :nth-child(1) > .related-widget-wrapper > .select2"
  )
    .click()
    .wait(3000)
    .get(".select2-container > .select2-dropdown > .select2-results > ul > li")
    .last()
    .click();
  cy.get(".field-location > :nth-child(1) > .related-widget-wrapper > .select2")
    .click()
    .wait(3000)
    .get(
      ".select2-container > .select2-dropdown > .select2-results > ul:first-child"
    )
    .click();
  cy.contains("Save").click();
  cy.get(".success").should("exist");
});

it("Creates meeting:complete", () => {
  cy.visit("/dj-admin");
  cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
  cy.get("#id_password").type("admin");
  cy.contains("Log in").click();
  cy.get("#user-tools > strong").should("have.text", "Ali");

  cy.get(".model-meeting > :nth-child(2) > .addlink").click();
  cy.get(
    ".field-meeting_type > :nth-child(1) > .related-widget-wrapper > .select2"
  )
    .click()
    .wait(3000)
    .get(".select2-container > .select2-dropdown > .select2-results > ul > li")
    .last()
    .click();
  cy.get("#id_additional_info").type(additional_info);
  cy.get("#id_start_date_0").type(start_date);
  cy.get("#id_start_date_1").type(start_time.substring(0,start_time.length-3));
  cy.get("#id_end_date_0").type(end_date);
  cy.get("#id_end_date_1").type(end_time.substring(0,start_time.length-3));
  cy.get(".field-location > :nth-child(1) > .related-widget-wrapper > .select2")
    .click()
    .wait(3000)
    .get(
      ".select2-container > .select2-dropdown > .select2-results > ul:first-child"
    )
    .click();
  cy.get("#id_external_enrollment_url").type(ext_enroll);
  cy.get(".field-is_public > .checkbox-row > .vCheckboxLabel").click();
  cy.get("#id_is_public").check();
  cy.get(".field-is_active > .checkbox-row > .vCheckboxLabel").click();
  cy.get("#id_is_active").check();
  cy.get('#id_announced_date_0').type(announced_date);
  cy.get('#id_announced_date_1').type(announced_time.substring(0,start_time.length-3))
  cy.contains("Save").click();

  cy.get(".success").should("exist");
});
