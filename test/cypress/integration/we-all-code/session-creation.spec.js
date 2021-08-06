import faker from "faker";

import { format } from "date-fns";


const location = faker.datatype.number({ min: 1, max: 3 });
const start_datetime = faker.date.between("2021-01-01","2023-12-31")
const course = faker.datatype.number({min: 17, max: 21})
const date = start_datetime.toLocaleDateString();
const time = start_datetime.toLocaleTimeString();

const capacity = faker.datatype.number({ min: 10, max: 50 });
const mentor_cap = faker.datatype.number({ min: 5, max: 25 });
const min_cost = faker.datatype.number(1000)
const max_cost = faker.datatype.number({min: min_cost, max: min_cost+1000})
const cost = faker.datatype.number({min:min_cost, max:max_cost})

const link = "zoom.example"
const id = faker.datatype.number({min:10000, max:99999})
const password = "weallcode"

describe("Creates sessions for a course: required fields", () => {
  it("Logs in", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();
    cy.get("#user-tools > strong").should("have.text", "Ali");
  });

  it("Creates Session: required fields", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();


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

    cy.get(".default").click();
    cy.get('.success').click();
  });
});

describe("Creates sessions for a course: complete", () => {
  it("Logs in", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();
    cy.get("#user-tools > strong").should("have.text", "Ali");
  });

  it("Creates Session", () => {
    cy.visit("/dj-admin");
    cy.get("#id_username").type("gregoriofs+admin@uchicago.edu");
    cy.get("#id_password").type("admin");
    cy.contains("Log in").click();

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
    cy.get("#id_is_public").check();
    cy.get('#id_online_video_link').type(link);
    cy.get('#id_online_video_meeting_id').type(id);
    cy.get('#id_online_video_meeting_password').type(password);
    cy.get('#id_cost').type(cost);
    cy.get('#id_minimum_cost').type(min_cost);
    cy.get('#id_maximum_cost').type(max_cost);
    cy.get(".default").click();
    cy.get('.success').click();

  });
});