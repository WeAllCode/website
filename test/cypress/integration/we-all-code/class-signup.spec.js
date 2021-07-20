// const { isSymbol } = require("cypress/types/lodash")

describe("Signup for Classes", () => {
    it("Mentor Signup", () => {

        cy.visit("/account/login")
        cy.get("#id_login").type("gregoriofs+mentor@uchicago.edu")
        cy.get("#id_password").type("mentor")
        cy.contains("Log in").click()
        cy.get(".margin-vertical-3 > .grid-container > .margin-top-3 > h2:first").should('have.text',"Your Profile")
        cy.contains("Programs").click()
        cy.get(':nth-child(3) > .medium-4 > .button').click();
        cy.get('p > .button').click();
        cy.get("body").then(($body) => {
            if($body.text().includes("Sign up to mentor for the")) {
                cy.contains("Yes, I'm excited").click()
            }
            else {
                cy.contains("Nevermind").click()
            }
        })

    })

    it("Parent Signup", () => {
        cy.visit("/account/login")
        cy.get("#id_login").type("gregoriofs+guardian@uchicago.edu")
        cy.get("#id_password").type("guardian")
        cy.contains("Log in").click()
        cy.get(".margin-vertical-3 > .grid-container > .margin-top-3 > h2").eq(1).should("have.text","Students")
        cy.contains("Programs").click()
        cy.get(':nth-child(2) > .medium-4 > .button').click();
        cy.get(':nth-child(3) > .text-right > .button').click();
        cy.get("body").then(($body) => {
                    if($body.text().includes("Enroll Kelly Doe for the")) {
                        cy.get(".margin-vertical-3 > .grid-container > .container > .title").should("have.text",'Enroll Kelly Doe for the "Choose Your Own Adventure" class on Jan. 1, 2022 from 10 a.m. to 1 p.m..')
                    }
                    else {
                        cy.get(".margin-vertical-3 > .grid-container > .container > .title").should("have.text",'Kelly Doe can no longer make it to the "Choose Your Own Adventure" class on Jan. 1, 2022 from 10 a.m. to 1 p.m..')
                    }
                })
        cy.get('button.button').click();
        cy.get(".padding-vertical-1 > .callout > strong").should("have.text","Well done!")
    })

    it("Nevermind Button Test", () => {
        cy.visit("/account/login")
        cy.get("#id_login").type("gregoriofs+guardian@uchicago.edu")
        cy.get("#id_password").type("guardian")
        cy.contains("Log in").click()
        cy.get(".margin-vertical-3 > .grid-container > .margin-top-3 > h2").eq(1).should("have.text","Students")
        cy.contains("Programs").click()
        cy.get(':nth-child(2) > .medium-4 > .button').click();
        cy.get(':nth-child(3) > .text-right > .button').click();
        cy.contains("Nevermind").click();
        cy.get(".padding-vertical-1 > .callout > strong").should("not.exist");
    })

    it("Unregisters Student", () => {
        cy.visit("/account/login")
        cy.get("#id_login").type("gregoriofs+guardian@uchicago.edu")
        cy.get("#id_password").type("guardian")
        cy.contains("Log in").click()
        cy.get(".margin-vertical-3 > .grid-container > .margin-top-3 > h2").eq(1).should("have.text","Students")
        cy.get(':nth-child(1) > :nth-child(4) > .button').click();
        cy.get('.form > .tertiary').click();

    })

    it("Unregister Mentor", () => {
        cy.visit("/account/login")
        cy.get("#id_login").type("gregoriofs+mentor@uchicago.edu")
        cy.get("#id_password").type("mentor")
        cy.contains("Log in").click()
        cy.get(".margin-vertical-3 > .grid-container > .margin-top-3 > h2:first").should('have.text',"Your Profile")
        cy.get('tr > :nth-child(3) > .button').click();
        cy.get('.form > .tertiary').click();
        cy.contains("Can't make it").should("not.exist")
    })

    it("Edit student info", () => {
        cy.visit("/account/login")
        cy.get("#id_login").type("gregoriofs+guardian@uchicago.edu")
        cy.get("#id_password").type("guardian")
        cy.contains("Log in").click()
        cy.get(".margin-vertical-3 > .grid-container > .margin-top-3 > .students > tbody > tr:first").contains('Edit Info').click()
        cy.get("#id_medical_conditions").type("None")
        cy.contains("Update").click()
        cy.get(".padding-vertical-1 > .callout > strong").should("have.text","Well done!")

    })
})
