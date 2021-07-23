/// <reference types="cypress" />

// const faker = require("faker");
import faker from "faker";

import { format } from "date-fns";

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
    ethnicity: faker.datatype.number({ min: 1, max: 5 }),
    password: faker.internet.password(),
    birthday: format(
      faker.date.between(birthday_min, birthday_max),
      "yyyy-MM-dd"
    ),
    address: faker.address.streetAddress(true),
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
    cy.get("#id_race_ethnicity").select([`${parent.ethnicity}`]);
    cy.get("#id_birthday").type(parent.birthday);
    cy.contains("Continue").click();
    // TODO: Check for success message

    // Student
    cy.get("#id_first_name").type(student.first_name);
    cy.get("#id_last_name").type(student.last_name);
    cy.get("#id_birthday").type(student.birthday);
    // cy.get(":nth-child(5) > .control-label").click();
    cy.get("#id_gender").type(student.gender);
    cy.get(
      `#id_race_ethnicity > :nth-child(${student.ethnicity}) > label`
    ).click();
    cy.get("#id_school_name").type("Example School");
    cy.get("#id_school_type > :nth-child(1) > label").click();
    cy.get("#id_school_type_0").check();
    cy.get("#id_medical_conditions").type("None");
    cy.get("#id_medications").type("None");
    cy.get("#id_photo_release").check();
    cy.get(":nth-child(11) > .checkbox > label").click();
    cy.get("#id_consent").check();
    cy.get(".submit").click();

    // TODO: Check for success message
  });
});

describe("Signup User", () => {
  it("signup invalid user with error", () => {
    cy.get("#main .title").contains("Thanks for registering");
  });

  it("Volunteer Signup", () => {
    // TODO: update to use new date format
    const volunteer = randomPerson();
    volunteer.workplace = faker.company.companyName();

    cy.contains("Volunteer").click();

    /* ==== Generated with Cypress Studio ==== */
    cy.get("#id_bio").type("Lorem ipsum");

    cy.get("#id_birthday").type(volunteer_birthday());

    cy.get("#id_gender").type(gender);

    cy.get("#id_work_place").type(workplace);

    cy.get("#id_phone").type(phone);

    cy.get("#id_home_address").type(address);

    cy.get("#id_race_ethnicity").select([`${ethnicity}`]);
    cy.get(".submit").click();
    /* ==== End Cypress Studio ==== */
  });
});
