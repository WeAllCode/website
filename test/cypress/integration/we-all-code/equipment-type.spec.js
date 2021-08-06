import faker from "faker";

it("Creates equipment type", () => {
  cy.visit("/dj-admin");
  cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
  cy.get("#id_password").type("admin");
  cy.contains("Log in").click();
  cy.get("#user-tools > strong").should("have.text", "Ali");
  
  const type = faker.commerce.product()

  cy.get('.model-equipmenttype > :nth-child(2) > .addlink').click();
  cy.get('#id_name').type(type);
  cy.get('.default').click();
  cy.get('.success').should('exist');
})