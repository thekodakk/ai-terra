"""Expand our own model depth without changing its initial outputs."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import torch
from .model import TerraModel
from .training import atomic_save, load_checkpoint


def expand_depth(model, layers):
    if not model.cfg.layers < layers <= 16:
        raise ValueError('Yeni katman sayısı mevcut sayıdan büyük ve en fazla 16 olmalı.')
    grown = TerraModel(replace(model.cfg, layers=layers)).to(next(model.parameters()).device)
    # Existing blocks, embeddings and final norm retain the user's own weights.
    grown.load_state_dict(model.state_dict(), strict=False)
    with torch.no_grad():
        for block in grown.blocks[model.cfg.layers:]:
            # Both residual branches initially contribute exactly zero. Their
            # internal projections remain independently randomly initialized.
            block.proj.weight.zero_()
            block.proj.bias.zero_()
            block.mlp[2].weight.zero_()
            block.mlp[2].bias.zero_()
    return grown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--layers',type=int,default=16)
    args = parser.parse_args()
    source, output = Path(args.source), Path(args.output)
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Büyütülen model için yeni bir dosya seç.')
    torch.manual_seed(2026)
    torch.set_num_threads(4)
    model, info = load_checkpoint(source)
    grown = expand_depth(model,args.layers)
    payload = {k:v for k,v in info.items() if k not in ('optimizer','rng')}
    payload.update(config=grown.config_dict(), weights=grown.state_dict(),
                   parameters=sum(p.numel() for p in grown.parameters()),
                   parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   growth={'source_layers':model.cfg.layers, 'target_layers':args.layers,
                           'source_parameters':sum(p.numel() for p in model.parameters()),
                           'inherited_training_steps':info['steps'],
                           'method':'append_identity_residual_blocks', 'new_layer_steps':0})
    atomic_save(payload,output)
    summary = {k:v for k,v in payload.items() if k not in ('weights','conversation_pairs','followup_links')}
    output.with_suffix('.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'parameters':payload['parameters'],'growth':payload['growth']}))


if __name__ == '__main__':
    main()
