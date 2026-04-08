# Automatic Performance Optimization

This is an experiment to have claude code to keep optimizing the performance of the framework tqsdk-python (current repo) based on cProfile results.

## Plan
You are given the source code of tqsdk-python, a backtest framework for Chinese CTA futures market, and a script to run backtest of a strategy by calling the sdk. You need to keep analyzing the profile data from cProfile, and find ways to improve the system performance.

## Setup
You are working in two repos:
1. `./tqsdk`: contains tqsdk-python's complete source code.
2. `./harness_engineering`, which has its own virtual environment and contains backtest code using the current repo (it's `tqsdk-python` in its uv environment is pointing to the current repo)

To set up a new experiment, work with the user to:
**Start by running the first profiling**. run `cd harness_engineering && uv run python -m cProfile -o result.prof backtest.py`

Once you get confirmation, kick off the experimentation.

## Experimentation

### Step 1: Analyze the existing cProfile result and find ways to improve the repo's performance.
Look at the git state: the current branch/commit we're on.

Then run this command to get the backtest's top 10 functions sorted by tottime: `cd harness_engineering && uv run python -c "import pstats; p = pstats.Stats('result.prof'); p.sort_stats('tottime').print_stats(10)"`

Then optimize the current repo's code based on the cProfile result. 

**What you CAN do:**
Analyze and modify the code in `./tqsdk` however you want.

**What you CANNOT do:**
- Modify anything in `./harness_engineering`

**The goal is simple: get the lowest total backtest time, while keeping its backtest result exactly the same.**

### Step 2. Verify the optimization
Run the following command to profile the result:
`cd harness_engineering && uv run python -m cProfile -o new_result.prof backtest.py`

Two things to verify:
1. The result backtest time is shorter than previous.
2. The following backtest metrics MUST BE exactly the same as the backtest result(other metrics we don't care):
```
{'currency': 'CNY', 'pre_balance': 9165485.597521082, 'static_balance': 9165485.597521082, 'balance': 9165485.597521082, 'available': 9165485.097521082, 'ctp_balance': nan, 'ctp_available': nan, 'float_profit': 33099.99999999999, 'position_profit': 0.0, 'close_profit': 0.0, 'frozen_margin': 0.0, 'margin': 0.5, 'frozen_commission': 0.0, 'commission': 0.0, 'frozen_premium': 0.0, 'premium': 0.0, 'deposit': 0.0, 'withdraw': 0.0, 'risk_ratio': 5.455248330052814e-08, 'market_value': 0.0, '_tqsdk_stat': <tqsdk.entity.Entity object at 0x7d789e3fc9b0>, D({'start_date': '2025-01-01', 'end_date': '2025-12-31', 'init_balance': np.float64(10000000.0), 'balance': np.float64(9165485.597521082), 'start_balance': np.float64(10000000.0), 'end_balance': np.float64(9165485.597521082), 'ror': np.float64(-0.08345144024789186), 'annual_yield': np.float64(-0.08541331095548088), 'trading_days': 244, 'cum_profit_days': np.int64(92), 'cum_loss_days': np.int64(151), 'max_drawdown': np.float64(0.10702989218181808), 'commission': np.float64(14.40250000000001), 'open_times': 14403, 'close_times': 14402, 'daily_risk_ratio': np.float64(5.674929510006093e-08), 'max_cont_profit_days': np.int64(6), 'max_cont_loss_days': np.int64(11), 'sharpe_ratio': np.float64(-1.9706534357067889), 'calmar_ratio': np.float64(-0.0663809545753567), 'sortino_ratio': np.float64(-1.6926465451120536), 'tqsdk_punchline': '不要灰心，少侠重新来过', 'profit_volumes': 11850, 'loss_volumes': 60160, 'profit_value': np.float64(8928950.000000276), 'loss_value': np.float64(-9796549.999999123), 'winning_rate': 0.16456047771142898, 'profit_loss_ratio': np.float64(4.62718335334115)})}
```

If both are true,
1. use the new cProfile result for the next round and run: `cd harness_engineering && mv new_result.prof result.prof`
2. git commit with the improvement and the reduced time.

If either one is not true, then abandon the current change and start over from step 1.

### LOOP FOREVER
The idea is that you are a completely autonomous performance engineer trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate.
