describe("Login Page", () => {
  beforeEach(() => {
    cy.visit("/account/login/");
    cy.get("#djHideToolBarButton").click();
  });

  it("Bad User Login", function () {
    // Username
    cy.get("input[name=login]")
      .type("baduser@email.com")
      .should("have.value", "baduser@email.com");

    // Password
    cy.get("input[name=password]")
      .type("badpassword")
      .should("have.value", "badpassword");

    // Login button
    cy.contains("Log in").click();

    // Error
    cy.get(".errorlist").should("exist");
  });

  it("Login with Guardian account", () => {
    // Username
    cy.get("input[name=login]")
      .type("guardian@sink.sendgrid.net")
      .should("have.value", "guardian@sink.sendgrid.net");

    // Password
    cy.get("input[name=password]")
      .type("guardian")
      .should("have.value", "guardian");

    // Login button
    cy.contains("Log in").click();

    // we should be redirected to /account;
    cy.url().should("include", "/account");

    // our auth cookie should be present
    cy.getCookie("sessionid").should("exist");

    // UI should reflect this user being logged in
    cy.get("#id_first_name").should("have.value", "John");
    cy.get("#id_last_name").should("have.value", "Doe");
  });

  it("Login with Mentor account", () => {
    // Username
    cy.get("input[name=login]")
      .type("mentor@sink.sendgrid.net")
      .should("have.value", "mentor@sink.sendgrid.net");

    // Password
    cy.get("input[name=password]")
      .type("mentor")
      .should("have.value", "mentor");

    // Login button
    cy.contains("Log in").click();

    // we should be redirected to /account;
    cy.url().should("include", "/account");

    // our auth cookie should be present
    cy.getCookie("sessionid").should("exist");

    // UI should reflect this user being logged in
    cy.get("#id_first_name").should("have.value", "Daniel");
    cy.get("#id_last_name").should("have.value", "Conrad");
  });
});
