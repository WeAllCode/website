/// <reference types="cypress" />

const faker = require("faker");

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
    cy.get("#id_login").type("guardian@sink.sendgrid.net");
    cy.get("#id_password").type("guardian");
    cy.get("#login-form").submit();

    cy.location().should((loc) => {
      expect(loc.pathname).to.eq("/account/");
    });
  });

  it("login valid volunteer user", () => {
    cy.visit("/account/login/");
    cy.get("#id_login").type("mentor@sink.sendgrid.net");
    cy.get("#id_password").type("mentor");
    cy.get("#login-form").submit();
    cy.location().should((loc) => {
      expect(loc.pathname).to.eq("/account/");
    });
  });

  it("login valid admin user", () => {
    cy.visit("/account/login/");
    cy.get("#id_login").type("admin@sink.sendgrid.net");
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

describe("Signup User", () => {
  it("signup invalid user with error", () => {
    const first_name = faker.name.firstName();
    const last_name = faker.name.lastName();
    const email = faker.internet.email();
    const password = faker.internet.password();

    cy.visit("/account/signup/");
    cy.get("#id_email").type(email);
    cy.get("#id_first_name").type(first_name);
    cy.get("#id_last_name").type(last_name);
    cy.get("#id_password1").type(password);
    cy.get("#id_password2").type(password);
    cy.get("main form").submit();
  });
});
