# -*- coding: utf-8 -*-
"""
Module: test_hardware_advisor.py
Project: TALOS v5.18.0
Description:
    Unit tests for the HardwareModelAdvisor (v5.16.2). Verifies the
    piecewise 4-bit-quantization VRAM parameter budget, role-based model
    recommendations, hardware profile key contract, and the SOTA discovery
    radar. The budget and recommendation arithmetic is pure and tested
    without a GPU; hardware/network access is mocked to keep every test
    hermetic.

Dependencies:
    - pytest: Test framework.
    - unittest.mock: Patching hardware and network probes.
"""

from unittest.mock import patch

from src.core.hardware_advisor import HardwareModelAdvisor


class TestVramBudget:
    """Verify the piecewise parameter-budget formula."""

    def test_high_vram_budget(self):
        assert HardwareModelAdvisor.calculate_vram_budget(12.0) == 14.0
        assert HardwareModelAdvisor.calculate_vram_budget(24.0) == 14.0
        assert HardwareModelAdvisor.calculate_vram_budget(11.0) == 14.0

    def test_mid_vram_budget(self):
        assert HardwareModelAdvisor.calculate_vram_budget(8.0) == 8.0
        assert HardwareModelAdvisor.calculate_vram_budget(5.5) == 8.0
        assert HardwareModelAdvisor.calculate_vram_budget(10.9) == 8.0

    def test_low_vram_budget(self):
        assert HardwareModelAdvisor.calculate_vram_budget(4.0) == 3.0
        assert HardwareModelAdvisor.calculate_vram_budget(2.0) == 3.0

    def test_none_vram_budget(self):
        assert HardwareModelAdvisor.calculate_vram_budget(None) == 3.0


def _advisor_with_vram(vram_gb):
    """Return an advisor whose hardware profile is stubbed to a fixed VRAM."""
    advisor = HardwareModelAdvisor()
    advisor.get_hardware_profile = lambda: {
        "has_cuda": vram_gb >= 4.0,
        "device_name": "NVIDIA GeForce RTX 4070" if vram_gb >= 4.0 else "CPU",
        "total_vram_gb": vram_gb,
        "system_ram_gb": 16.0,
        "is_laptop_cpu": False,
    }
    return advisor


class TestRecommendations:
    """Verify role-based model sizing across VRAM tiers."""

    def test_high_vram_recommendations(self):
        recs = _advisor_with_vram(12.0).get_recommendations()
        assert recs["max_params_billions"] == 14.0
        assert recs["reasoning_local"] == "qwen2.5:14b"
        assert recs["screening_local"] == "llama3.1:8b"
        assert recs["reasoning_cloud"] == "deepseek-reasoner"
        assert recs["fast_cloud"] == "gemini-2.5-flash"

    def test_mid_vram_recommendations(self):
        recs = _advisor_with_vram(8.0).get_recommendations()
        assert recs["max_params_billions"] == 8.0
        assert recs["reasoning_local"] == "qwen2.5:7b"

    def test_cpu_recommendations(self):
        recs = _advisor_with_vram(0.0).get_recommendations()
        assert recs["max_params_billions"] == 3.0
        assert recs["reasoning_local"] == "qwen2.5:3b"


class TestHardwareProfile:
    """Verify the hardware profile key contract (graceful CPU fallback)."""

    def test_profile_keys(self):
        profile = HardwareModelAdvisor().get_hardware_profile()
        expected = {
            "has_cuda", "device_name", "total_vram_gb",
            "system_ram_gb", "is_laptop_cpu",
        }
        assert expected.issubset(set(profile.keys()))


class TestSotaRadar:
    """Verify the SOTA radar filters models by the detected budget."""

    def test_scan_sota_filters_by_budget(self):
        advisor = _advisor_with_vram(12.0)
        with patch.object(advisor, "_scan_ollama_tags", return_value=set()), \
             patch.object(advisor, "_scan_openrouter_models", return_value=[]):
            results = advisor.scan_sota_models(timeout=0.1)
        assert isinstance(results, list)
        assert len(results) > 0
        names = {r["name"] for r in results}
        assert "qwen2.5:14b" in names
        maverick = next(r for r in results if r["name"] == "llama4:maverick")
        assert maverick["fits_budget"] is False
        qwen14 = next(r for r in results if r["name"] == "qwen2.5:14b")
        assert qwen14["fits_budget"] is True
