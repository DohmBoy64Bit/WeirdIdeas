"""
Tests for authentication and character creation
"""
import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_signup(self, test_credentials):
        """Test user signup"""
        resp = requests.post(f"{BASE_URL}/auth/signup", json=test_credentials)
        assert resp.status_code == 200
        assert "access_token" in resp.json()
    
    def test_login(self, test_credentials, auth_token):
        """Test user login"""
        resp = requests.post(f"{BASE_URL}/auth/login", json=test_credentials)
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert resp.json()["access_token"] == auth_token
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "nonexistent",
            "password": "wrong"
        })
        assert resp.status_code == 401

class TestCharacterCreation:
    """Test character creation"""
    
    def test_create_character_zenkai(self, auth_headers):
        """Test creating a Zenkai character"""
        resp = requests.post(f"{BASE_URL}/players/", json={
            "name": "TestZenkai",
            "race": "Zenkai"
        }, headers=auth_headers)
        
        assert resp.status_code == 200
        player = resp.json()
        assert player["race"] == "Zenkai"
        assert "flux" in player["stats"]
        assert player["stats"]["flux"] == player["stats"]["max_flux"]
    
    def test_create_character_vitalis(self, auth_headers):
        """Test creating a Vitalis character"""
        resp = requests.post(f"{BASE_URL}/players/", json={
            "name": "TestVitalis",
            "race": "Vitalis"
        }, headers=auth_headers)
        
        assert resp.status_code == 200
        player = resp.json()
        assert player["race"] == "Vitalis"
        # Vitalis should have higher flux
        assert player["stats"]["max_flux"] > 100
    
    def test_flux_initialization(self, test_player):
        """Test that flux is properly initialized"""
        assert "flux" in test_player["stats"]
        assert "max_flux" in test_player["stats"]
        assert test_player["stats"]["flux"] == test_player["stats"]["max_flux"]
        
        # Zenkai base flux is 80, plus INT*5
        expected_flux = 80 + (test_player["stats"]["int"] * 5)
        assert test_player["stats"]["max_flux"] == expected_flux
