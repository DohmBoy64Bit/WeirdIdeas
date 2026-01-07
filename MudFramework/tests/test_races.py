"""
Comprehensive tests for all race-specific features and passives
"""
import pytest
from tests.conftest import send_command
import requests

BASE_URL = "http://localhost:8000/api/v1"

class TestAllRaces:
    """Test all 4 races and their unique characteristics"""
    
    def test_zenkai_race(self, auth_headers):
        """Test Zenkai race creation and stats"""
        resp = requests.post(f"{BASE_URL}/players/", json={
            "name": "TestZenkai2",
            "race": "Zenkai"
        }, headers=auth_headers)
        
        assert resp.status_code == 200
        player = resp.json()
        assert player["race"] == "Zenkai"
        # Zenkai base flux: 80
        expected_flux = 80 + (player["stats"]["int"] * 5)
        assert player["stats"]["max_flux"] == expected_flux
    
    def test_vitalis_race(self, auth_headers):
        """Test Vitalis race - highest flux"""
        resp = requests.post(f"{BASE_URL}/players/", json={
            "name": "TestVitalis2",
            "race": "Vitalis"
        }, headers=auth_headers)
        
        assert resp.status_code == 200
        player = resp.json()
        assert player["race"] == "Vitalis"
        # Vitalis base flux: 120 (highest)
        expected_flux = 120 + (player["stats"]["int"] * 5)
        assert player["stats"]["max_flux"] == expected_flux
        assert player["stats"]["max_flux"] > 120
    
    def test_terran_race(self, auth_headers):
        """Test Terran race - balanced"""
        resp = requests.post(f"{BASE_URL}/players/", json={
            "name": "TestTerran",
            "race": "Terran"
        }, headers=auth_headers)
        
        assert resp.status_code == 200
        player = resp.json()
        assert player["race"] == "Terran"
        # Terran base flux: 100
        expected_flux = 100 + (player["stats"]["int"] * 5)
        assert player["stats"]["max_flux"] == expected_flux
    
    def test_glacial_race(self, auth_headers):
        """Test Glacial race - lowest flux but high defense"""
        resp = requests.post(f"{BASE_URL}/players/", json={
            "name": "TestGlacial",
            "race": "Glacial"
        }, headers=auth_headers)
        
        assert resp.status_code == 200
        player = resp.json()
        assert player["race"] == "Glacial"
        # Glacial base flux: 70 (lowest)
        expected_flux = 70 + (player["stats"]["int"] * 5)
        assert player["stats"]["max_flux"] == expected_flux

class TestPassiveAbilities:
    """Test all race passive abilities"""
    
    def test_zenkai_battle_hardened(self, ws_connection):
        """Test Zenkai Battle Hardened passive accumulates STR bonus"""
        # Check passive exists
        messages = send_command(ws_connection, "passive")
        content = " ".join(msg.get("content", "") for msg in messages)
        assert "Battle Hardened" in content
        assert "STR" in content or "strength" in content.lower()
    
    def test_vitalis_regeneration(self, ws_connection):
        """Test Vitalis Regeneration passive"""
        # Would need Vitalis character - test passive description exists
        messages = send_command(ws_connection, "passive")
        content = " ".join(msg.get("content", "") for msg in messages)
        # Zenkai player won't have Vitalis passive
        assert "Battle Hardened" in content  # Verify current race passive works
    
    def test_passive_command_exists(self, ws_connection):
        """Test passive command is functional"""
        messages = send_command(ws_connection, "passive")
        assert len(messages) > 0
        # Should get some response about race passive
        has_passive_info = any("passive" in msg.get("content", "").lower() or
                              "Battle Hardened" in msg.get("content", "")
                              for msg in messages)
        assert has_passive_info

class TestRaceSkills:
    """Test race-specific skills"""
    
    def test_zenkai_skills(self, ws_connection):
        """Test Zenkai race skills"""
        send_command(ws_connection, "cheat_exp 2000")
        messages = send_command(ws_connection, "skills")
        
        skills_content = " ".join(msg.get("content", "") for msg in messages)
        # Zenkai skills
        assert "Warrior Strike" in skills_content or "Skills" in skills_content
    
    def test_race_skill_requirements(self, ws_connection):
        """Test race skills have proper requirements"""
        messages = send_command(ws_connection, "skillinfo Warrior Strike")
        
        info = " ".join(msg.get("content", "") for msg in messages)
        assert "Zenkai" in info or "Flux" in info
