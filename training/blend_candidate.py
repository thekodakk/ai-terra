"""Experimental interpolation of two related, locally trained checkpoints.

This is a candidate only; activation requires the ordinary regression gates.
"""
import hashlib
from pathlib import Path
from scratch.training import atomic_save, load_checkpoint


def main():
    base_path = Path('models/terra-trained.pt')
    candidate_path = Path('models/terra-natural-candidate.pt')
    _, base = load_checkpoint(base_path)
    _, candidate = load_checkpoint(candidate_path)
    if base['config'] != candidate['config']:
        raise ValueError('Architectures differ')
    base_hash = hashlib.sha256(base_path.read_bytes()).hexdigest()
    if candidate.get('parent_sha256') != base_hash:
        raise ValueError('Only a direct fine-tuning descendant may be blended')
    candidate['weights'] = {key: base['weights'][key].lerp(value, .5)
                            for key,value in candidate['weights'].items()}
    candidate.pop('optimizer', None)
    candidate['train_loss'] = None
    candidate['weight_interpolation'] = {
        'base_sha256':base_hash,
        'candidate_sha256':hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
        'candidate_fraction':.5,
        'note':'Historical steps retained; interpolated weights require fresh evaluation.'}
    atomic_save(candidate, 'models/terra-natural-blended.pt')


if __name__ == '__main__':
    main()
