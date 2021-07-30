import faker from "faker";

const datetime = faker.date.between("2021-01-01","2023-12-31");
const date = datetime.toLocaleDateString();
const time = datetime.toLocaleTimeString();

describe("Creates sessions for a course", () => {
    beforeEach( () => {
      cy.visit("/dj-admin");
      cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
      cy.get("#id_password").type("admin");
      cy.contains("Log in").click();
      cy.get("#user-tools > strong").should("have.text", "Ali");
    });

    it("Creates Student Order", () => {
      cy.get('.model-order > :nth-child(2) > .addlink').click();
     
      cy.get('.field-guardian > :nth-child(1) > .related-widget-wrapper > .select2').click().wait(3000).get('.select2-container > .select2-dropdown > .select2-results > ul > li').last().click();
      cy.get('.breadcrumbs').click();
      cy.get('.field-session > :nth-child(1) > .related-widget-wrapper > .select2').click().wait(3000).get('.select2-container > .select2-dropdown > .select2-results > ul > li').last().click();
      // cy.get('.select2-container > .select2-dropdown > .select2-results > .select2-results__options > li:last-child').click();
      cy.get('.field-student > :nth-child(1) > .related-widget-wrapper > .select2').click().wait(3000).get('.select2-container > .select2-dropdown > .select2-results > ul > li').last().click();
      cy.get('.vDateField').type(date);
      cy.get('.vTimeField').type(time.substring(0, time.length - 3));
      cy.get('#id_affiliate').type('Affiliate');
      cy.get('.submit-row > input[name="_save"]').click();
    });

    it("Creates Mentor Order", () => {
      
      cy.get('.model-mentororder > :nth-child(2) > .addlink').click();
      cy.get('.field-mentor > :nth-child(1) > .related-widget-wrapper > .select2').click().wait(3000).get('.select2-container > .select2-dropdown > .select2-results > ul:first-child').click();
      cy.get('.breadcrumbs').click();
      cy.get('.field-session > :nth-child(1) > .related-widget-wrapper > .select2').click().wait(3000).get('.select2-container > .select2-dropdown > .select2-results > ul > li').last().click();
      cy.get('.vDateField').type(date);
      cy.get('.vTimeField').type(time.substring(0, time.length - 3));
      cy.get('#id_affiliate').type('Affiliate');

      cy.get('.default').click();
    })
});   