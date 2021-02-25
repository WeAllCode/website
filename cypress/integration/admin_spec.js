// Admin
describe("Authenticated sections", () => {
  before(() => {
    cy.visit("/dj-admin/login/");
    cy.get("[name=csrfmiddlewaretoken]")
      .should("exist")
      .should("have.attr", "value")
      .as("csrfToken");

    cy.get("@csrfToken").then((token) => {
      console.log(token);
      cy.request({
        method: "POST",
        url: "/dj-admin/login/",
        form: true,
        body: {
          username: "admin@sink.sendgrid.net",
          password: "admin",
        },
        headers: {
          "X-CSRFTOKEN": token,
        },
      });
    });

    cy.getCookie("sessionid").should("exist");
    cy.getCookie("csrftoken").should("exist");
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce("sessionid", "csrftoken");
  });

  it("should do something", () => {
    // your test here
    // it's authenticated from now on!
  });

  it("should do something", () => {
    // your test here
    // it's authenticated from now on!
  });
});
