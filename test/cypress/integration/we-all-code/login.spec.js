/// <reference types="cypress" />

describe("Login User", () => {
  it("login invalid user with error", () => {
    cy.visit("/account/login/");
    cy.get("#id_login").type("invalid@user.com");
    cy.get("#id_password").type("invalid");
    cy.get("#login-form").submit();
    cy.get(".errorlist").should("exist");
  });

  it("login valid guardian user", () => {
    cy.visit("/account/login/");
    cy.get("#id_login").type("gregoriofs+guardian@uchicago.edu");
    cy.get("#id_password").type("guardian");
    cy.get("#login-form").submit();

    cy.location().should((loc) => {
      expect(loc.pathname).to.eq("/account/");
    });
  });

  it("login valid volunteer user", () => {
    cy.visit("/account/login/");
    cy.get("#id_login").type("gregoriofs+mentor@uchicago.edu");
    cy.get("#id_password").type("mentor");
    cy.get("#login-form").submit();
    cy.location().should((loc) => {
      expect(loc.pathname).to.eq("/account/");
    });
  });

  it("login valid admin user", () => {
    cy.visit("/account/login/");
    cy.get("#id_login").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.get("#login-form").submit();
    cy.location().should((loc) => {
      expect(loc.pathname).to.eq("/account/");
    });
  });
});

describe("Logout User", () => {
  it("logout user", () => {
    cy.visit("/account/logout/");
    cy.location().should((loc) => {
      expect(loc.pathname).to.eq("/");
    });
  });
});
