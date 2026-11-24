"""train.py <data.npz> <out> [folds] [epochs]: trains the small network of scorereader.headnet (filled head, hollow
head, no head) on the crops of build.py, with JAX on the CPU (pip install jax optax; a few minutes for 70,000 crops).

folds > 1: one network for each fold of whole hymns, each tested on the hymns that it never saw; writes
<out>.fold<i>.params.npz, the held-out probabilities <out>.oof.npy and the fold of each hymn <out>.folds.json.
folds == 1: one network on everything, <out>.params.npz: the weights that the reader is given (SCOREREADER_HEADNET).
JAX is needed for training only. The reader runs the network with NumPy and OpenCV."""
import json
import sys
import time

import jax
import jax.numpy as jnp
import numpy as np
import optax

data, out = sys.argv[1], sys.argv[2]
FOLDS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
EPOCHS = int(sys.argv[4]) if len(sys.argv) > 4 else 8
d = np.load(data)
X = d['X'].astype(np.float32)[:, None] / 255.0
Y = d['Y'].astype(np.int32)
G = d['G']
SHAPES = [('c1', (16, 1, 3, 3)), ('c2', (32, 16, 3, 3)), ('c3', (64, 32, 3, 3)), ('d1', (1024, 64)), ('d2', (64, 3))]
WEIGHT = jnp.array([1.0, 1.0, 3.0])     # a mark that is no note is rarer than a head: it weighs three times


def init(key):
    p = {}
    for name, shape in SHAPES:
        key, k = jax.random.split(key)
        fan = np.prod(shape[1:]) if name.startswith('c') else shape[0]
        p[name] = jax.random.normal(k, shape) * np.sqrt(2.0 / fan)
        p[name + 'b'] = jnp.zeros(shape[0] if name.startswith('c') else shape[1])
    return p


def forward(p, x):
    for c in ('c1', 'c2', 'c3'):
        x = jax.lax.conv_general_dilated(x, p[c], (1, 1), 'SAME', dimension_numbers=('NCHW', 'OIHW', 'NCHW'))
        x = jax.nn.relu(x + p[c + 'b'][None, :, None, None])
        x = jax.lax.reduce_window(x, -jnp.inf, jax.lax.max, (1, 1, 2, 2), (1, 1, 2, 2), 'VALID')
    x = jax.nn.relu(x.reshape(x.shape[0], -1) @ p['d1'] + p['d1b'])
    return x @ p['d2'] + p['d2b']


def loss(p, x, y):
    return jnp.mean(optax.softmax_cross_entropy_with_integer_labels(forward(p, x), y) * WEIGHT[y])


opt = optax.adam(1e-3)


@jax.jit
def step(p, s, x, y):
    value, grad = jax.value_and_grad(loss)(p, x, y)
    update, s = opt.update(grad, s, p)
    return optax.apply_updates(p, update), s, value


predict = jax.jit(lambda p, x: jax.nn.softmax(forward(p, x)))


def shift(batch, rng):
    """Each crop moved by up to two pixels and made a little paler or darker."""
    moved = np.zeros_like(batch)
    for i in range(len(batch)):
        dx, dy = rng.integers(-2, 3, 2)
        moved[i] = np.roll(np.roll(batch[i], dy, axis=1), dx, axis=2)
    return moved * rng.uniform(0.8, 1.2, (len(batch), 1, 1, 1)).astype(np.float32)


def fit(idx, seed=0):
    rng = np.random.default_rng(seed)
    p = init(jax.random.PRNGKey(seed))
    s = opt.init(p)
    for epoch in range(EPOCHS):
        order, started, losses = rng.permutation(idx), time.time(), []
        for b in range(0, len(order) - 255, 256):
            bi = order[b:b + 256]
            p, s, value = step(p, s, jnp.asarray(shift(X[bi], rng)), jnp.asarray(Y[bi]))
            losses.append(float(value))
        print(f'  epoch {epoch} loss {np.mean(losses):.4f} {time.time() - started:.0f}s', flush=True)
    return p


def save(p, path):
    np.savez(path, **{k: np.asarray(v) for k, v in p.items()})


if FOLDS > 1:
    groups = sorted(set(G))
    np.random.default_rng(1).shuffle(groups)
    fold_of = {g: i % FOLDS for i, g in enumerate(groups)}
    fold = np.array([fold_of[g] for g in G])
    oof = np.zeros((len(X), 3), np.float32)
    for f in range(FOLDS):
        train, test = np.where(fold != f)[0], np.where(fold == f)[0]
        print(f'fold {f}: train {len(train)} test {len(test)}', flush=True)
        p = fit(train, f)
        oof[test] = np.concatenate([np.asarray(predict(p, jnp.asarray(X[test[b:b + 1024]]))) for b in range(0, len(test), 1024)])
        save(p, f'{out}.fold{f}.params.npz')
        print('  held-out accuracy', float((oof[test].argmax(1) == Y[test]).mean()), flush=True)
    np.save(out + '.oof.npy', oof)
    json.dump(fold_of, open(out + '.folds.json', 'w'))
else:
    save(fit(np.arange(len(X))), out + '.params.npz')
