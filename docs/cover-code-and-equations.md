# The equations and the code behind the models

Text only, for the page. The code is quoted from the repository (file named above each block); lines marked `# ...` were trimmed. The equations are the same operations written as maths.

---

## 1. Equations

### Yearly model (Hong Kong rainfall)

| Step | Equation |
|---|---|
| Standardise the six yearly features | z = (x − μ) / σ |
| Covariance and its eigenvectors (PCA) | C = ZᵀZ / n,   C vⱼ = λⱼ vⱼ |
| The same by singular values | Z = U Σ Vᵀ,   λⱼ = Σⱼ² / n |
| Rebuild each year from k = 2 components | ẑ = Z Vₖ Vₖᵀ |
| Reconstruction error (the anomaly) | e = ‖ z − ẑ ‖² = Σᵢ (zᵢ − ẑᵢ)² |
| Rescale to 0–1 across the fitted years | s = (e − e_min) / (e_max − e_min) |
| Return period of the yearly peak (Gumbel) | P(R′ ≥ r) = 1 − exp( −exp( −(r − μ) / β ) ),   T = 1 / P |

### Moving-window model

| Step | Equation |
|---|---|
| Rank a measure among windows ending at the same time of year (±15 days) | pᵢ = ( rank(xᵢ) − ½ ) / n |
| Turn the rank into a bounded score | uᵢ = Φ⁻¹(pᵢ),  clipped to [−3.5, 3.5] |
| Centre the scores | C = U − ū |
| Components that keep 80% of the variance | k = min { k : Σⱼ≤ₖ λⱼ / Σⱼ λⱼ ≥ 0.80 } |
| Coordinates in the kept components | t = C Vₖ |
| Distance inside the kept components (Mahalanobis) | d² = Σⱼ≤ₖ tⱼ² / λⱼ |
| Distance off the components (reconstruction) | e = ‖ C − t Vₖᵀ ‖² |
| Rank of a window among all N windows | r = ( rank(d²) − ½ ) / N |
| Rarity, "one window in …" | 1 / (1 − r),   u = −log₁₀(1 − r) |
| Score rule at 30 days | score = max( rank(d²), rank(e) ) |
| Score rule at 365 days | score = rank(d²) |

### Checking against documented events

| Step | Equation |
|---|---|
| How an event ranks among spans of the same length | percentile = share of other spans whose highest score is below the event's highest score |
| Chance | 0.5 |

### Valence and arousal (Hong Kong)

| Step | Equation |
|---|---|
| Two factors from a varimax-rotated PCA | storminess, wetness |
| Departure from a normal year | departure = √( max(storminess, 0)² + wetness² ) |
| Percentile rank among the n fitted years | pct(v) = ( rank(v) − ½ ) / n |
| Arousal | A = ½ ( pct(storminess) + pct(anomaly) ) |
| Valence | V = 1 − 2 · pct( ½ ( pct(departure) + pct(anomaly) ) ) |

### Human-Water Interface (L'Aire)

| Step | Equation |
|---|---|
| Seasonal norm for a calendar day | m(d) = median of log₁₀ Q over the fitting years, pooling days within ±15 of d |
| Seasonal spread | σ(d) = max( stdev of that pool, 0.05 ) |
| Distance from the norm | a = log₁₀ Q − m(d) |
| In units of the season's spread | z = a / σ(d) |
| Day score | PCA with k = 3 components on seven daily features; e = ‖ z − ẑ ‖² |
| Calibration check | share of held-out days with e above the training 95th percentile ≈ 0.05 |

---

## 2. Code

### The yearly model: PCA and the reconstruction error — `noea/climate_pulse/rainfall/anomaly.py`

```python
X_raw = np.array([_feature_row(yp) for yp in complete_years])

scaler = StandardScaler().fit(X_raw)
X = scaler.transform(X_raw)

pca = PCA(n_components=n_components).fit(X)
X_reconstructed = pca.inverse_transform(pca.transform(X))
errors = np.sum((X - X_reconstructed) ** 2, axis=1)
```

### Scoring a year the model has never seen — same file

```python
x = self.scaler.transform([_feature_row(yp)])
reduced = self.pca.transform(x)
reconstructed = self.pca.inverse_transform(reduced)
error = float(np.sum((x - reconstructed) ** 2))
return max(0.0, min(1.0, (error - self.score_min) / (self.score_max - self.score_min)))
```

### The return period of the peak — `noea/climate_pulse/rainfall/frameworks.py`

```python
loc, scale = gumbel_r.fit(r_vals)
exceedance_prob = gumbel_r.sf(r, loc=loc, scale=scale)     # P(R' >= r)
out[y] = min(1.0 / exceedance_prob, 1e5) if exceedance_prob > 0 else 1e5
```

### The moving-window model — `noea/climate_pulse/windows.py`

```python
def seasonal_probit(ends, F):
    # rank each measure among windows that end at the same time of year (+-15 days),
    # then turn the rank into a bounded probit: a measure that is nearly constant
    # in a season cannot blow up
    r = (rankdata(F[near, j]) - 0.5) / len(near)
    Z[here, j] = np.clip(norm.ppf(r[at]), -3.5, 3.5)

Z = seasonal_probit(ends, F)
C = Z - Z.mean(0)
_, S, Vt = np.linalg.svd(C, full_matrices=False)
var = S ** 2 / len(C)
k = int(np.searchsorted(np.cumsum(var) / var.sum(), VARIANCE_KEPT) + 1)    # VARIANCE_KEPT = 0.80
scores = C @ Vt[:k].T
maha = ((scores ** 2) / var[:k]).sum(1)
recon = ((C - scores @ Vt[:k]) ** 2).sum(1)
rank = lambda v: (rankdata(v) - 0.5) / len(v)
score = rank(maha) if scoring == "mahalanobis" else np.maximum(rank(maha), rank(recon))
```

### The seasonal norm — `noea/human_water_interface/baselines.py`

```python
for d, v in zip(ts.dates, ts.values):
    if d.year in self.fit_years and v > 0:
        by_idx[day_index(d)].append(math.log10(v))
for i in range(1, 367):
    pool = []
    for off in range(-self.window, self.window + 1):
        pool += by_idx[(i - 1 + off) % 366 + 1]
    self.median[i] = statistics.median(pool)
    self.spread[i] = max(statistics.pstdev(pool), 0.05)

def anomaly(self, d, value):
    return math.log10(max(value, 1e-6)) - self.median[day_index(d)]

def z(self, d, value):
    return self.anomaly(d, value) / self.spread[day_index(d)]
```

### Valence and arousal — `noea/climate_pulse/rainfall/affect.py`

```python
pct = lambda v: (rankdata(v) - 0.5) / n
surprise = np.array([anomaly.normalized(y.year) for y in years])
departure = np.sqrt(np.maximum(storminess, 0) ** 2 + wetness ** 2)
arousal = (pct(storminess) + pct(surprise)) / 2
valence = 1 - 2 * pct((pct(departure) + pct(surprise)) / 2)
```

---

## 3. Short versions for the cover

The yearly model in four lines:

```python
X = StandardScaler().fit_transform(X_raw)
pca = PCA(n_components=2).fit(X)
X_hat = pca.inverse_transform(pca.transform(X))
errors = np.sum((X - X_hat) ** 2, axis=1)
```

The error as one equation:

```
e = || z - z V Vᵀ ||²
```

The moving-window model in five lines:

```python
_, S, Vt = np.linalg.svd(C, full_matrices=False)
var = S ** 2 / len(C)
k = int(np.searchsorted(np.cumsum(var) / var.sum(), 0.80) + 1)
scores = C @ Vt[:k].T
maha = ((scores ** 2) / var[:k]).sum(1)
```
