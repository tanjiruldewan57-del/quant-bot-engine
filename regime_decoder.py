"""
MarketRegimeViterbiDecoder
Production-grade Hidden Markov Model (HMM) Viterbi Decoder 
Decodes latent market regimes (Calm_Bull vs Turbulent_Bear) without lookahead bias.
"""
import numpy as np

class MarketRegimeViterbiDecoder:
    """
    Production-grade Hidden Markov Model (HMM) Viterbi Decoder 
    to reconstruct the optimal sequence of latent market regimes.
    Defines 2 Latent States:
        - State 0 (Calm_Bull): Low volatility, positive drift.
        - State 1 (Turbulent_Bear): High volatility, negative/flat drift.
    """
    def __init__(self, states=None, transition_matrix=None, emission_means=None, emission_covars=None, start_probs=None):
        self.states = states or ['Calm_Bull', 'Turbulent_Bear']
        self.N = len(self.states)
        self.A = np.array(transition_matrix if transition_matrix is not None else [
            [0.90, 0.10],  # State 0 -> State 0, State 0 -> State 1
            [0.15, 0.85]   # State 1 -> State 0, State 1 -> State 1
        ])
        self.means = np.array(emission_means if emission_means is not None else [
            [0.0005, 0.012],   # Calm State: Positive return, low volatility
            [-0.0015, 0.045]   # Turbulent State: Negative return, high volatility
        ])
        self.covars = np.array(emission_covars if emission_covars is not None else [
            [[1e-6, 0.0], [0.0, 1e-5]], # Covariance structures for State 0
            [[1e-5, 0.0], [0.0, 1e-4]]  # Covariance structures for State 1
        ])
        self.pi = np.array(start_probs if start_probs is not None else [0.70, 0.30])
        
    def _multivariate_gaussian_log_pdf(self, y, mean, covar, min_covar=1e-6):
        """
        Calculates multivariate Gaussian log probability density with diagonal 
        covariance regularization to prevent singularity (det -> 0) and arithmetic underflow.
        """
        d = len(y)
        covar = np.array(covar, copy=True)
        covar_det = np.linalg.det(covar)
        
        # REGULARIZATION: If the determinant collapses, apply covariance eigenvalue floor
        if covar_det <= 1e-15:
            covar += min_covar * np.eye(d)
            covar_det = np.linalg.det(covar)
            
        covar_inv = np.linalg.inv(covar)
        diff = y - mean
        quadratic_form = -0.5 * np.dot(diff.T, np.dot(covar_inv, diff))
        log_normalization = -0.5 * (d * np.log(2 * np.pi) + np.log(covar_det))
        return log_normalization + quadratic_form

    def decode(self, observations):
        """
        Computes the single most likely path of hidden market states.
        observations: T x D matrix, where T is time steps and D is feature dimension (returns, volatility).
        """
        T = len(observations)
        if T == 0:
            return []
        viterbi_log = np.zeros((self.N, T))
        backpointer = np.zeros((self.N, T), dtype=int)
        
        # 1. Initialization (t = 0)
        for s in range(self.N):
            log_emit = self._multivariate_gaussian_log_pdf(observations[0], self.means[s], self.covars[s])
            viterbi_log[s, 0] = np.log(self.pi[s]) + log_emit
            backpointer[s, 0] = 0
            
        # 2. Dynamic Programming Recursion
        for t in range(1, T):
            for s in range(self.N):
                log_emit = self._multivariate_gaussian_log_pdf(observations[t], self.means[s], self.covars[s])
                
                candidate_probs = [
                    viterbi_log[prev_s, t-1] + np.log(self.A[prev_s, s]) + log_emit
                    for prev_s in range(self.N)
                ]
                
                viterbi_log[s, t] = max(candidate_probs)
                backpointer[s, t] = np.argmax(candidate_probs)
                
        # 3. Path Backtracking (Terminating Step)
        optimal_state_path = np.zeros(T, dtype=int)
        optimal_state_path[-1] = np.argmax(viterbi_log[:, -1])
        
        for t in range(T-2, -1, -1):
            optimal_state_path[t] = backpointer[optimal_state_path[t+1], t+1]
            
        return [self.states[idx] for idx in optimal_state_path]

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 VITERBI HMM REGIME DECODER - UNIT VERIFICATION")
    print("=" * 60)
    decoder = MarketRegimeViterbiDecoder()
    
    # Mock observation series: [Log Return, Volatility]
    sample_feed = np.array([
        [0.0006, 0.011],
        [0.0004, 0.013],
        [-0.0050, 0.038], 
        [-0.0085, 0.048],
        [-0.0020, 0.042],
        [0.0010, 0.015]
    ])
    
    regimes = decoder.decode(sample_feed)
    print("Sample Market Observations (Return, Vol):")
    for row in sample_feed:
        print(f"  {row}")
    print("\nDecoded Regime Sequence:")
    for idx, r in enumerate(regimes):
        print(f"  Tick #{idx + 1}: {r}")
