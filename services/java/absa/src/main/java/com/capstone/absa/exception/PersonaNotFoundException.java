package com.capstone.absa.exception;

public class PersonaNotFoundException extends RuntimeException {
    public PersonaNotFoundException(String id) {
        super("Persona not found with id: " + id);
    }
}
