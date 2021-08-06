import faker from "faker";

describe("Add a location", () => {
  it("Creates a location", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();
    cy.get("#user-tools > strong").should("have.text", "Ali");

    const name = faker.lorem.word(6);
    const address = faker.address.streetAddress();
    const city = faker.address.cityName();
    const state = faker.address.stateAbbr();
    const zip_code = faker.address.zipCode();

    cy.get('.model-location > :nth-child(2) > .addlink').click();
    cy.get('#id_name').type(name);
    cy.get('#id_address').type(address);
    cy.get('#id_city').type(city);
    cy.get('.field-state').click();
    cy.get('#id_state').type(state);
    cy.get('#id_zip').type(zip_code);
    cy.get('.default').click();
    cy.get('.success').should('exist');
  });
});