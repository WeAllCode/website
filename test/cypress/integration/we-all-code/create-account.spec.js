/// <reference types="cypress" />

const faker = require("faker");

describe("Signup User", () => {
  beforeEach(() => {
    const first_name = faker.name.firstName();
    const last_name = faker.name.lastName();
    const email = faker.internet.exampleEmail(first_name,last_name);
    const password = faker.internet.password();

    cy.visit("/account/signup/");
    cy.get("#id_email").type(email);
    cy.get("#id_first_name").type(first_name);
    cy.get("#id_last_name").type(last_name);
    cy.get("#id_password1").type(password);
    cy.get("#id_password2").type(password);
    cy.get("main form").submit();
  });

  it("signup invalid user with error", () => {
    cy.get("#main .title").contains("Thanks for registering");
  });

  it("Parent Signup", function () {

    const student_first_name = faker.name.firstName();
    const student_last_name = faker.name.lastName();
    const phone = faker.phone.phoneNumber();
    const birthday = isParent => {
      const max = isParent ? 2000 : 2005
      const min = isParent ? 1950 : 2013
      const year = Math.floor(Math.random() * (max - min + 1)) + min
      const month = Math.floor((Math.random() * 12)) + 1
      const formattedMonth = month < 10 ? `0${month}` : `${month}`
      const day = Math.floor((Math.random() * 27)) + 1
      const formattedDay = day < 10 ? `0${day}` : `${day}`
      return `${year}-${formattedMonth}-${formattedDay}`
    };
    const gender = faker.name.gender();
    const zip = faker.address.zipCode();
    const ethnicity = Math.floor(Math.random() * 5) + 1;

    cy.get(".medium-offset-2 > p > .button").click();

    cy.get("#id_phone").type(phone);

    cy.get("#id_zip").type(zip);

    cy.get("#id_gender").type("Male");
    cy.get("#id_race_ethnicity").select([`${ethnicity}`]);
    cy.get("#id_birthday").type(birthday(true))
    cy.contains("Continue").click();

    cy.get("#id_first_name").type(student_first_name);

    cy.get("#id_last_name").type(student_last_name);

    cy.get("#id_birthday").type(birthday(false));
    cy.get(":nth-child(5) > .control-label").click();

    cy.get("#id_gender").type(gender);
    cy.get(`#id_race_ethnicity > :nth-child(${ethnicity}) > label`).click();

    cy.get("#id_school_name").type("Example School");
    cy.get("#id_school_type > :nth-child(1) > label").click();
    cy.get("#id_school_type_0").check();
    cy.get("#id_medical_conditions").type('None');
    cy.get("#id_medications").type('None')
    cy.get("#id_photo_release").check();
    cy.get(":nth-child(11) > .checkbox > label").click();
    cy.get("#id_consent").check();
    cy.get(".submit").click();
    /* ==== End Cypress Studio ==== */
  });

  it("Volunteer Signup", () => {
    const volunteer_birthday = () => {
      const max = 2000
      const min = 1980
      const year = Math.floor(Math.random() * (max - min + 1)) + min
      const month = Math.floor((Math.random() * 12)) + 1
      const formattedMonth = month < 10 ? `0${month}` : `${month}`
      const day = Math.floor((Math.random() * 27)) + 1
      const formattedDay = day < 10 ? `0${day}` : `${day}`
      return `${year}-${formattedMonth}-${formattedDay}`
    };
    const gender = faker.name.gender();
    const workplace = faker.company.companyName();
    const phone = faker.phone.phoneNumber();
    const address = faker.address.streetAddress(true);
    const ethnicity = Math.floor(Math.random() * 5) + 1;

    cy.contains("Volunteer").click()

    /* ==== Generated with Cypress Studio ==== */
    cy.get('#id_bio').type("Lorem ipsum");

    cy.get('#id_birthday').type(volunteer_birthday());

    cy.get('#id_gender').type(gender);
 
    cy.get('#id_work_place').type(workplace);

    cy.get('#id_phone').type(phone);

    cy.get('#id_home_address').type(address);

    cy.get('#id_race_ethnicity').select([`${ethnicity}`]);
    cy.get('.submit').click();
    /* ==== End Cypress Studio ==== */
  })
});
