# -*- coding: utf-8 -*-
"""
Module: migrate_d3qn_checkpoint.py
Project: TALOS v5.18.2
Description:
    One-shot Net2Net tensor-surgery utility that migrates the trained DDDQN
    checkpoint ``models/dddqn_trained.pth`` from the legacy 14-source action
    space to the 18-source action space introduced in v5.15.4, preserving all
    previously trained weights exactly.

    The migration performs two complementary Net2WiderNet expansions:

    1. Output (advantage) head -- ``A.weight`` and ``A.bias`` are widened from
       ``[old_action_dim, 32]`` / ``[old_action_dim]`` to ``[19, 32]`` / ``[19]``
       (18 academic sources + 1 sleep action). Rows for sources that already
       exist in the legacy checkpoint are copied bit-for-bit. Rows for the four
       newly introduced sources (``openaire``, ``openreview``, ``nasa_ntrs``,
       ``hal_inria``) are initialised optimistically: the mean of the top-5
       existing source rows (ranked by L2 norm) plus a +0.05 exploratory bias.
       The sleep row is re-indexed from its legacy position to index 18.

    2. Input (feature) head -- ``lstm1.weight_ih_l0`` is widened from
       ``[512, old_state_dim]`` to ``[512, 25]``. Columns are remapped by
       source name; the two streak columns and the four provider columns are
       shifted to their new positions, and new source columns are initialised
       with the mean of the existing source columns (the standard Net2WiderNet
       replicate-then-specialise prior).

    The checkpoint metadata dictionary is updated in place (``state_dim=25``,
    ``action_dim=19``, ``source_names`` expanded to 18), and the result is
    verified by instantiating ``DuelingLSTM(input_dim=25, output_dim=19)`` and
    running ``load_state_dict(strict=True)``.

    v5.18.2: this utility is confirmed as the canonical Net2Net repair tool and
    is now idempotent -- re-running it against an already-migrated 18-source
    checkpoint verifies the strict load and exits without rewriting the file.

Dependencies:
    - torch: tensor loading, surgical expansion, and re-serialisation.
    - src.ai.drl.drl_networks.DuelingLSTM: canonical network for load verification.
"""
import os
import sys
import shutil

import torch

# -- Resolve the project root (walk up until talos.py is found). --
_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
while _PROJECT_ROOT and not os.path.exists(os.path.join(_PROJECT_ROOT, "talos.py")):
    _PROJECT_ROOT = os.path.dirname(_PROJECT_ROOT)
if _PROJECT_ROOT:
    sys.path.insert(0, _PROJECT_ROOT)

CHECKPOINT_PATH = os.path.join(_PROJECT_ROOT, "models", "dddqn_trained.pth")
BACKUP_PATH = CHECKPOINT_PATH + ".bak"

# -- Canonical 18-source academic mesh. The runtime observation order produced
#    by talos_env._load_source_list() is ALPHABETICAL (it sorts the config keys
#    ending in "_query"), so the target source list is the sorted canonical set.
CANONICAL_18_SOURCES = [
    "arxiv", "core", "crossref", "dblp", "elsevier", "hal_inria", "ieee",
    "nasa_ntrs", "openalex", "openarchives", "openaire", "openreview",
    "osti", "plos", "pubmed", "scigov", "semantic_scholar", "springer",
]
TARGET_SOURCES = sorted(CANONICAL_18_SOURCES)

_PROVIDER_COUNT = 4


def _locate_advantage_head(weights):
    """Find the final advantage linear layer's weight and bias tensors.

    The DuelingLSTM architecture names the dueling heads ``V`` (state value)
    and ``A`` (advantage). The advantage head is the linear layer whose output
    dimension equals the action dimension (old_action_dim = num_sources + 1).
    This helper locates it robustly by scanning for the 2-D weight tensor whose
    first dimension matches its own bias length and is larger than 1.

    Args:
        weights (dict): The state_dict (OrderedDict) from the checkpoint.

    Returns:
        tuple: (weight_key, bias_key, old_action_dim, hidden_dim).
    """
    candidates = []
    for key, tensor in weights.items():
        if tensor.dim() == 2 and key.endswith(".weight"):
            bias_key = key[:-len(".weight")] + ".bias"
            if bias_key in weights and weights[bias_key].dim() == 1:
                if tensor.shape[0] == weights[bias_key].shape[0] and tensor.shape[0] > 1:
                    candidates.append((key, bias_key, tensor.shape[0], tensor.shape[1]))

    if not candidates:
        raise RuntimeError("Could not locate the advantage head (A.weight / A.bias).")

    candidates.sort(key=lambda c: -c[2])
    weight_key, bias_key, action_dim, hidden_dim = candidates[0]
    return weight_key, bias_key, action_dim, hidden_dim


def migrate():
    """Execute the Net2Net checkpoint surgery and write the migrated file."""
    if not os.path.exists(CHECKPOINT_PATH):
        raise FileNotFoundError(
            "Checkpoint not found: {}. Run training first.".format(CHECKPOINT_PATH))

    # -- Safety backup (created exactly once, preserving the true original). --
    if not os.path.exists(BACKUP_PATH):
        shutil.copy2(CHECKPOINT_PATH, BACKUP_PATH)
        print("[BACKUP] Created safety backup: {}".format(BACKUP_PATH))
    else:
        print("[BACKUP] Existing backup found ({}); preserving original.".format(BACKUP_PATH))

    # -- Load the checkpoint dict (metadata + weights). --
    checkpoint = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, dict) or "weights" not in checkpoint:
        raise RuntimeError("Unsupported checkpoint format: expected dict with 'weights' key.")

    weights = checkpoint["weights"]
    old_state_dim = checkpoint.get("state_dim")
    old_action_dim = checkpoint.get("action_dim")
    old_source_names = list(checkpoint.get("source_names", []))
    network_class = checkpoint.get("network_class", "DuelingLSTM")

    print("[LOAD] network_class={} state_dim={} action_dim={} sources={}".format(
        network_class, old_state_dim, old_action_dim, len(old_source_names)))

    if old_action_dim != len(old_source_names) + 1:
        raise RuntimeError(
            "Checkpoint metadata inconsistency: action_dim={} but source_names={}".format(
                old_action_dim, len(old_source_names)))

    num_old_sources = len(old_source_names)
    new_action_dim = len(TARGET_SOURCES) + 1                          # 18 sources + sleep = 19
    new_state_dim = 1 + len(TARGET_SOURCES) + 2 + _PROVIDER_COUNT     # 25

    # -- v5.18.2: idempotency guard. When the checkpoint is already at the
    #    canonical 18-source / 25-dim layout, no surgery is required; verify a
    #    strict load and exit without rewriting the file. --
    if (num_old_sources == len(TARGET_SOURCES)
            and old_state_dim == new_state_dim
            and old_action_dim == new_action_dim):
        from src.ai.drl.drl_networks import DuelingLSTM
        _model = DuelingLSTM(input_dim=new_state_dim, output_dim=new_action_dim)
        _model.load_state_dict(weights)
        print("[VERIFY] Checkpoint already at canonical {} sources / {} state dims / {} actions; no surgery required.".format(
            num_old_sources, new_state_dim, new_action_dim))
        return

    # -- 1. Expand the advantage head (output layer). --
    adv_weight_key, adv_bias_key, adv_action_dim, hidden_dim = _locate_advantage_head(weights)
    if adv_action_dim != old_action_dim:
        print("[WARN] Advantage head dim ({}) != metadata action_dim ({}); trusting tensor.".format(
            adv_action_dim, old_action_dim))

    old_a_weight = weights[adv_weight_key]   # [old_action_dim, hidden]
    old_a_bias = weights[adv_bias_key]       # [old_action_dim]

    old_row_of = {name: i for i, name in enumerate(old_source_names)}

    # -- Optimistic prior: mean of the top-5 existing source rows (L2 norm). --
    source_rows = old_a_weight[:num_old_sources]
    norms = source_rows.norm(dim=1)
    top_k = min(5, num_old_sources)
    top5_mean = source_rows[torch.topk(norms, top_k).indices].mean(dim=0)
    mean_bias = old_a_bias[:num_old_sources].mean()

    new_a_weight = torch.zeros(new_action_dim, hidden_dim)
    new_a_bias = torch.zeros(new_action_dim)

    for tgt_idx, name in enumerate(TARGET_SOURCES):
        if name in old_row_of:
            old_idx = old_row_of[name]
            new_a_weight[tgt_idx] = old_a_weight[old_idx]
            new_a_bias[tgt_idx] = old_a_bias[old_idx]
        else:
            new_a_weight[tgt_idx] = top5_mean + 0.05
            new_a_bias[tgt_idx] = mean_bias

    # -- Sleep action: re-indexed from legacy last row to new last row. --
    new_a_weight[-1] = old_a_weight[num_old_sources]
    new_a_bias[-1] = old_a_bias[num_old_sources]

    # -- Verify bit-for-bit preservation of the surviving source rows. --
    for tgt_idx, name in enumerate(TARGET_SOURCES):
        if name in old_row_of:
            assert torch.equal(new_a_weight[tgt_idx], old_a_weight[old_row_of[name]]), \
                "Weight preservation failed for {}".format(name)
            assert torch.equal(new_a_bias[tgt_idx], old_a_bias[old_row_of[name]]), \
                "Bias preservation failed for {}".format(name)
    assert torch.equal(new_a_weight[-1], old_a_weight[num_old_sources]), "Sleep weight preservation failed"
    assert torch.equal(new_a_bias[-1], old_a_bias[num_old_sources]), "Sleep bias preservation failed"

    weights[adv_weight_key] = new_a_weight
    weights[adv_bias_key] = new_a_bias

    # -- 2. Expand the input head (LSTM first-layer feature columns). --
    input_key = "lstm1.weight_ih_l0"
    if input_key not in weights:
        raise RuntimeError("Input head tensor '{}' not found.".format(input_key))

    old_wih = weights[input_key]  # [4*hidden_lstm1, old_state_dim]
    if old_wih.shape[1] != old_state_dim:
        print("[WARN] lstm1.weight_ih_l0 input dim ({}) != metadata state_dim ({}).".format(
            old_wih.shape[1], old_state_dim))
        old_state_dim = old_wih.shape[1]

    if old_state_dim != 1 + num_old_sources + 2 + _PROVIDER_COUNT:
        raise RuntimeError(
            "Unexpected legacy state layout: state_dim={} for {} sources.".format(
                old_state_dim, num_old_sources))

    new_wih = torch.zeros(old_wih.shape[0], new_state_dim)

    # -- Hour column (index 0) is position-invariant. --
    new_wih[:, 0] = old_wih[:, 0]

    # -- Source columns: map by name, or use the column-mean prior for new. --
    old_source_col = {name: 1 + i for i, name in enumerate(old_source_names)}
    source_col_mean = old_wih[:, 1:1 + num_old_sources].mean(dim=1)

    for tgt_idx, name in enumerate(TARGET_SOURCES):
        col = 1 + tgt_idx
        if name in old_source_col:
            new_wih[:, col] = old_wih[:, old_source_col[name]]
        else:
            new_wih[:, col] = source_col_mean

    # -- Streak and provider columns: shift to their new trailing positions. --
    new_wih[:, len(TARGET_SOURCES) + 1] = old_wih[:, num_old_sources + 1]      # low streak
    new_wih[:, len(TARGET_SOURCES) + 2] = old_wih[:, num_old_sources + 2]      # error streak
    new_wih[:, len(TARGET_SOURCES) + 3:len(TARGET_SOURCES) + 7] = \
        old_wih[:, num_old_sources + 3:num_old_sources + 7]                    # 4 provider ratios

    weights[input_key] = new_wih

    # -- 3. Update checkpoint metadata. --
    checkpoint["state_dim"] = new_state_dim
    checkpoint["action_dim"] = new_action_dim
    checkpoint["source_names"] = list(TARGET_SOURCES)

    # -- 4. Save the migrated checkpoint. --
    torch.save(checkpoint, CHECKPOINT_PATH)
    print("[SAVE] Migrated checkpoint written: {}".format(CHECKPOINT_PATH))

    # -- 5. Verify clean strict load into the canonical 18-source network. --
    from src.ai.drl.drl_networks import DuelingLSTM

    model = DuelingLSTM(input_dim=new_state_dim, output_dim=new_action_dim)
    reloaded = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=True)
    model.load_state_dict(reloaded["weights"])  # strict=True by default

    assert reloaded["state_dim"] == new_state_dim
    assert reloaded["action_dim"] == new_action_dim
    assert len(reloaded["source_names"]) == len(TARGET_SOURCES)

    print("[VERIFY] DuelingLSTM(input_dim={}, output_dim={}) loaded strictly with zero mismatch.".format(
        new_state_dim, new_action_dim))
    print("[DONE] Net2Net migration complete: {} -> {} sources, {} -> {} actions, {} -> {} state dims.".format(
        num_old_sources, len(TARGET_SOURCES), old_action_dim, new_action_dim, old_state_dim, new_state_dim))


if __name__ == "__main__":
    migrate()

