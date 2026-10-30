---
name: nn-from-scratch
description: Build, train and debug neural networks from first principles rather than by reaching for a framework default. Use when implementing an autograd engine, a character level language model, an MLP, BatchNorm, a WaveNet style hierarchical net or a small GPT; when writing a manual backward pass; and above all when a net trains badly and the cause is init scaling, saturated activations, a broadcasting bug, a wrong learning rate or a dead layer. Also use when asked to explain backpropagation, autograd, cross entropy, batch normalisation or tokenisation at the level of the actual arithmetic. Carries the diagnostics (activation and gradient histograms, the update to data ratio) and the measured results from Karpathy's Neural Networks Zero to Hero, including the places where the principled fix did not beat the hacky one.
license: MIT
---

# Neural networks from scratch

Distilled from `karpathy/nn-zero-to-hero` (MIT), lectures 1 to 8. Every number below was read out of those notebooks, not recalled. The course itself is videos plus seven notebooks; what follows is the transferable method, not a summary of the videos.

## The one idea that matters

**Build the smallest thing that still contains the mechanism, and look inside it while it runs.** A scalar autograd engine over single floats shows everything backprop does. A bigram table shows everything a language model does. Scale comes last and changes nothing conceptually. A net you cannot inspect is a net you cannot debug, so the histograms below are not optional extras: they are how you see.

The matching failure is reaching for `nn.Module` and an optimiser before you can say what the gradient of your loss with respect to one weight is.

## Workflow

Work up this ladder. Each rung is the previous one with one new idea, and skipping rungs is what produces a net nobody can debug.

1. **Scalar autograd.** A `Value` holding `data`, `grad`, `_prev`, `_op` and a `_backward` closure. Implement `+`, `*`, `tanh`, `exp`, `**`. Backward is a topological sort of the graph, reversed, calling each node's `_backward`.
2. **Counting model.** A bigram table, normalised to probabilities. No gradients at all. This fixes what the loss means before any learning happens.
3. **The same model by gradient descent.** One linear layer over one hot inputs reaches the same loss as the counting table. That equivalence is the proof your training loop works.
4. **MLP.** Embedding table, concatenated context, hidden tanh layer, output logits. Introduce minibatches, a train/dev/test split and learning rate search.
5. **Look inside it.** Activation and gradient histograms per layer, and the update to data ratio. Fix init before touching architecture.
6. **Manual backward pass.** Backprop the whole MLP by hand, no `loss.backward()`. This is the rung that turns gradients from magic into arithmetic.
7. **Deeper and structured.** A hierarchical, WaveNet style net, and containers (`Sequential`, `Flatten`) you wrote yourself.
8. **Attention, then tokenisation.** A small GPT, then Byte Pair Encoding, which is where a surprising share of LLM misbehaviour actually originates.

## Rules that came from a real bug

### Autograd

- **Accumulate gradients, never assign.** `self.grad += ...`, not `=`. A node used twice in the graph gets two contributions, and assignment silently keeps one. This is the single most common autograd bug.
- **Zero the gradients before every backward pass.** Carrying the previous step's gradient is a bug that still trains, just worse, which makes it hard to see.
- **Backward order is a reverse topological sort.** Not insertion order, not recursion without a visited set.

### Broadcasting

- **`keepdim=True` on every sum or max you divide by.** `probs = counts / counts.sum(1, keepdim=True)` normalises rows. Drop `keepdim` and the shape becomes `(n,)`, which broadcasts along the wrong axis and normalises columns. It does not error. It trains. It is wrong. `keepdim` appears 22 times in the manual backprop lecture alone, which tells you how central it is.
- **Read every broadcast out loud** as shapes aligning from the right, with 1s stretched. Most tensor bugs are a broadcast you did not intend.

### Initialisation, before anything else

- **Know the loss you should start at.** For a uniform guess over `V` classes it is `-ln(1/V)`. For 27 characters that is about 3.30. A much higher starting loss means the logits are large and confidently wrong at init, and the first few hundred steps are spent undoing that rather than learning.
- **Squash the output layer at init.** Scale the final weights down (and zero the final bias) so logits start near zero.
- **Do not saturate tanh.** Plot the hidden activations at init. If most `|h|` are near 1, the tanh derivative `1 - h²` is near 0 and those neurons pass no gradient. A unit that is saturated for every example in the batch is dead.
- **Kaiming init, as actually written:** `torch.randn(fan_in, fan_out) * gain / fan_in**0.5`, with `gain = 5/3` for tanh. The `fan_in**0.5` keeps activation variance stable through depth; the gain compensates for the squashing.

### Diagnostics, which are the real deliverable

Three plots tell you nearly everything:

1. **Activation histogram per layer.** Want a stable spread across depth. Collapsing toward zero or piling up at ±1 are both failures.
2. **Gradient histogram per layer.** Want comparable scale across layers. Shrinking with depth is vanishing gradient.
3. **Update to data ratio**, `(lr * p.grad).std() / p.data.std()`, log10, per parameter tensor, over training. **Target about 1e-3**, which is −3 on a log10 plot. Far below means that tensor is learning too slowly; far above means it is being thrown around.

### Learning rate

- **Find it, do not guess it.** Sweep the exponent over a range (`lre` from about −3 to 0), plot loss against it, and take the value just before loss turns up.
- **Decay late.** The course runs 200,000 steps at batch size 32 with `lr = 0.1` for the first 150,000 steps, then `0.01`.

### BatchNorm, and its real cost

- **It couples examples.** A single example's output now depends on the other examples in its batch. That is a strange property to accept and the source of subtle train/inference divergence.
- **Keep running mean and variance** for inference, or calibrate them in a pass at the end.
- **A bias before a BatchNorm is a no-op**, because BN subtracts the mean. Drop it and keep BN's own `beta`.

### The honest result, which most summaries get wrong

From the lecture 3 loss log, same net, validation loss:

| Change | train | val |
|---|---|---|
| original | 2.1245 | 2.1682 |
| fix confidently wrong softmax | 2.07 | 2.13 |
| fix saturated tanh at init | 2.0356 | **2.1027** |
| "semi-principled" kaiming init | 2.0377 | 2.1070 |
| add BatchNorm | 2.0668 | 2.1048 |

**The principled fixes did not beat the hand-tuned ones.** Kaiming came out marginally worse than the hacky scaling it replaced, and BatchNorm worse than both. They are still right to adopt, because they remove hyperparameters and keep working as the net gets deeper, where hand tuning stops scaling. Report this honestly when you make such a change: the gain is robustness, not loss.

### Manual backward passes

- **Work backwards cell by cell and check each one** against autograd with an exact comparison, not just `allclose`.
- **A broadcast forward is a sum backward**, over exactly the dimensions that were stretched, with `keepdim` to restore the shape.
- **Cross entropy collapses.** Backpropagating softmax and log separately is fiddly and numerically worse; the fused gradient is `probs - onehot(targets)`, over the batch.

### Tokenisation

Treat it as its own stage with its own training data and algorithm (BPE), not a preprocessing detail. A large share of odd LLM behaviour (arithmetic, spelling, trailing whitespace, non-English text) traces back to it rather than to the model.

## Verification checklist

Before claiming a net works:

- Initial loss matches `-ln(1/V)`, or you can say why not.
- Activation and gradient histograms plotted per layer, at init and during training.
- Update to data ratio sits near 1e-3 for every parameter tensor.
- Learning rate chosen by a sweep you can show, not inherited.
- Overfit a single batch to near zero loss first. A net that cannot overfit 32 examples has a bug, not a capacity problem.
- Train, dev and test kept separate, and the number you report is dev or test, never train.
- Any manual gradient checked against autograd.

## Source

`karpathy/nn-zero-to-hero` (MIT): lectures 1 to 8. Lectures 1 to 6 ship as notebooks in `lectures/`; lectures 7 (GPT) and 8 (tokenizer) live in `karpathy/nanoGPT` and `karpathy/minbpe` and linked Colabs, not in that repo. Figures above are from `makemore_part3_bn.ipynb`.
