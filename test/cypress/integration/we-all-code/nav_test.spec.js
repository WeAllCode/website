describe("Test navigation links", () => {
  it("Tests every page on nav bar", () => {
    cy.visit("/");
    const pages = ["Our Story", "Programs", "Team", "Join Us", "Log In"];
    pages.forEach((currentPage) => {
      const url =
        currentPage === "Log In"
          ? "/account/login"
          : currentPage.replace(/\s+/g, "-").toLowerCase();
      cy.visit(`/${url}/`);

      pages.forEach((page) => {
        if (page !== currentPage) {
          cy.contains(page).click();
          const url =
            page === "Log In"
              ? "login"
              : page.replace(/\s+/g, "-").toLowerCase();
          cy.url().should("include", url);
          cy.go("back");
        }
      });
    });
  });

  it("Tests links in footer", () => {
    cy.visit("/");
    const pages = ["Our Story", "Programs", "Team", "Join Us"];
    pages.forEach((page) => {
      const url = page.replace(/\s+/g, "-").toLowerCase();
      cy.visit(`/${url}/`);
      pages.forEach((currentPage) => {
        cy.get("footer > nav > .grid-container > .grid-x")
          .children()
          .contains(currentPage)
          .click();
        const url = currentPage.replace(/\s+/g, "-").toLowerCase();
        cy.url().should("include", url);
        cy.go("back");
      });
    });
  });
});
