import faker from "faker";

import { format } from "date-fns";

describe("Creates sessions for a course", () => {
  it("Logs in", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();
    cy.get("#user-tools > strong").should("have.text", "Ali");
    /* ==== Generated with Cypress Studio ==== */

    /* ==== End Cypress Studio ==== */
  });
  it("Creates Session", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();

    // const course = faker.datatype.number({ min: 15, max: 23 });
    const location = faker.datatype.number({ min: 1, max: 3 });
    const datetime = faker.date.between("2021-01-01","2023-12-31")
    const course = faker.datatype.number({min: 17, max: 23})
    const date = datetime.toLocaleDateString();
    const time = datetime.toLocaleTimeString();
    const capacity = faker.datatype.number({ min: 10, max: 50 });
    const mentor_cap = faker.datatype.number({ min: 5, max: 25 });

    cy.get(".model-session > :nth-child(2) > .addlink").click();
    cy.get("#id_course").select(`${course}`);
    cy.get("#id_location").select(`${location}`);
    cy.get("#id_start_date_0").clear();
    cy.get("#id_start_date_0").type(date);
    cy.get("#id_start_date_1").clear();
    cy.get("#id_start_date_1").type(time.substring(0, time.length - 3));
    cy.get("#id_capacity").clear();
    cy.get("#id_capacity").type(capacity);
    cy.get("#id_mentor_capacity").clear();
    cy.get("#id_mentor_capacity").type(mentor_cap);
    cy.get("#id_instructor").select("1");
    cy.get("#id_assistant_from").select(["94"]);
    cy.get("#id_assistant_add_link").click();
    cy.get("#id_is_active").check();
    cy.get(".default").click();
  });
});
