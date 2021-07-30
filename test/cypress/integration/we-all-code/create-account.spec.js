/// <reference types="cypress" />

// const faker = require("faker");
import faker from "faker";

import { format } from "date-fns";

const race = ["White","Black","Asian","American Indian", "Native Hawaiin", "Middle Eastern"]
const ethnicity = ["Hispanic", "Not Hispanic"]

function randomPerson(
  birthday_min = "1950-01-01",
  birthday_max = "2000-01-01"
) {
  const person = {
    first_name: faker.name.firstName(),
    last_name: faker.name.lastName(),
    gender: faker.name.gender(),
    phone: faker.phone.phoneNumber(),
    zip: faker.address.zipCode(),
    ethnicity: faker.datatype.number({ min: 0, max: 1 }),
    password: faker.internet.password(),
    school:`${faker.lorem.word(7)} School`,
    birthday: format(
      faker.date.between(birthday_min, birthday_max),
      "yyyy-MM-dd"
    ),
    address: faker.address.streetAddress(true),
    race: faker.datatype.number({ min: 0, max: 4}),
  };

  person.email = faker.internet.exampleEmail(
    person.first_name,
    person.last_name
  );

  return person;
}

describe("Create Parent Account", () => {
  beforeEach(() => {
    const user = randomPerson();

    cy.visit("/account/signup/");
    cy.get("#id_email").type(user.email);
    cy.get("#id_first_name").type(user.first_name);
    cy.get("#id_last_name").type(user.last_name);
    cy.get("#id_password1").type(user.password);
    cy.get("#id_password2").type(user.password);
    cy.get("main form").submit();
  });

  it("fill out parent information", function () {
    const student = randomPerson("2005-01-01", "2013-01-01");
    const parent = randomPerson();
  
    cy.get(".medium-offset-2 > p > .button").click();

    // Parents
    cy.get("#id_phone").type(parent.phone);
    cy.get("#id_zip").type(parent.zip);
    cy.get("#id_gender").type("Male");
    cy.get("#id_race_ethnicity").select([`${parent.ethnicity + 1}`]);
    cy.get("#id_birthday").type(parent.birthday);
    cy.contains("Continue").click();
    // TODO: Check for success message
    cy.get("#main > .grid-container > .medium-padding-horizontal-3 > h2").should("have.text","Register your first student now")
    // Student
    cy.get("#id_first_name").type(student.first_name);
    cy.get("#id_last_name").type(student.last_name);
    cy.get("#id_birthday").type(student.birthday);
    cy.get("#id_gender").type(student.gender);
    cy.get('#id_race').select(race[student.race]);
    cy.get('#id_ethnicity').select(ethnicity[student.ethnicity]);
    cy.get('#id_school_name').type(student.school);
    cy.get('#id_school_type_0').check();
    cy.get(':nth-child(8) > .control-label').click();
    cy.get('#id_medical_conditions').click();
    cy.get('#id_medications').click();
    cy.get(':nth-child(11) > .checkbox > label').click();
    cy.get('#id_photo_release').check();
    cy.get(':nth-child(12) > .checkbox > label').click();
    cy.get('#id_consent').check();
    cy.get('.submit').click();
    // TODO: Check for success message
    cy.get("#main > .grid-container > .medium-padding-horizontal-3 > h4").should("have.text","1 Student Registered ")
  });
});

describe("Signup Volunteer", () => {
  

  it("Volunteer Signup", () => {

    const volunteer = randomPerson();
    volunteer.workplace = faker.company.companyName();

    cy.visit("/account/signup/");
    cy.get("#id_email").type(volunteer.email);
    cy.get("#id_first_name").type(volunteer.first_name);
    cy.get("#id_last_name").type(volunteer.last_name);
    cy.get("#id_password1").type(volunteer.password);
    cy.get("#id_password2").type(volunteer.password);
    cy.get("main form").submit();

    cy.contains("Volunteer").click();

    /* ==== Generated with Cypress Studio ==== */
    cy.get("#id_bio").type("Lorem ipsum");

    cy.get("#id_birthday").type(volunteer.birthday);

    cy.get("#id_gender").type(volunteer.gender);

    cy.get("#id_work_place").type(volunteer.workplace);

    cy.get("#id_phone").type(volunteer.phone);

    cy.get("#id_home_address").type(volunteer.address);

    cy.get("#id_race_ethnicity").select([`${volunteer.ethnicity + 1}`]);
    
    cy.get(".submit").click();
    /* ==== End Cypress Studio ==== */
  });
});
