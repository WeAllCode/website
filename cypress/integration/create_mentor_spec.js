describe("Create Mentor", () => {
  // Hide the django debug bar
  beforeEach(() => {
    cy.visit("/");
    cy.get("#djHideToolBarButton").click();
  });

  it("Create Account", function () {
    const email = `test_mentor_${Math.floor(Math.random() * 100)}@example.com`;
    const password = "thisisapasswordforbobdole";
    const firstName = "Bob";
    const lastName = "Dole";

    // Login button
    cy.contains("Log In").click();
    cy.contains("Register now").click();

    // Fill out form
    cy.get("#id_email").type(email);
    cy.get("#id_first_name").type(firstName);
    cy.get("#id_last_name").type(lastName);
    cy.get("#id_password1").type(password);
    cy.get("#id_password2").type(password);

    cy.get("[type='submit']").click();

    // Choose volunteer
    cy.contains("Volunteer").click();

    // TODO: Doesn't work from here on...

    // cy.get("#id_birthday").click().type("01/01/1990");
    // cy.get("#id_race_ethnicity").select(["2"]);
    // cy.get("#id_gender").type("Male");
    // cy.get(".submit").click();
  });
});
