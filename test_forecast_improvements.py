"""
Test script for forecast accuracy improvements.
Tests the accuracy module and enhanced forecast functionality.
"""

import sys
sys.path.insert(0, '/Users/adnanquraishee/Downloads/finqorp')

from modules import accuracy, forecast
import numpy as np

print("=" * 60)
print("TESTING FORECAST ACCURACY IMPROVEMENTS")
print("=" * 60)

# Test 1: Accuracy Metrics Calculation
print("\n1. Testing accuracy metrics calculation...")
actual = np.array([100, 102, 101, 105, 103, 107])
predicted = np.array([100, 101, 102, 104, 104, 106])

metrics = accuracy.calculate_metrics(actual, predicted)
print(f"   RMSE: ${metrics['RMSE']:.2f}")
print(f"   MAE: ${metrics['MAE']:.2f}")
print(f"   MAPE: {metrics['MAPE']:.2f}%")
print(f"   Directional Accuracy: {metrics['Directional_Accuracy']:.1f}%")

avg_price = np.mean(actual)
score = accuracy.get_accuracy_score(metrics, avg_price)
print(f"   Overall Accuracy Score: {score:.1f}/100")

if 0 <= score <= 100:
    print("   ✅ PASS: Accuracy score in valid range")
else:
    print("   ❌ FAIL: Accuracy score out of range")

# Test 2: Backtest Function
print("\n2. Testing backtest on AAPL (30-day forecast)...")
print("   This may take 10-20 seconds...")

try:
    results = accuracy.run_backtest('AAPL', forecast_days=30, num_simulations=100)
    
    if 'error' in results:
        print(f"   ❌ FAIL: Backtest returned error: {results['error']}")
    else:
        print("   ✅ PASS: Backtest completed successfully")
        print(f"   Accuracy Score: {results['accuracy_score']:.1f}/100")
        print(f"   RMSE: ${results['metrics']['RMSE']:.2f}")
        print(f"   MAE: ${results['metrics']['MAE']:.2f}")
        print(f"   MAPE: {results['metrics']['MAPE']:.2f}%")
        print(f"   Directional Accuracy: {results['metrics']['Directional_Accuracy']:.1f}%")
        print(f"   Test period: {results['forecast_days']} days")
        
        # Validate results
        if results['accuracy_score'] >= 0 and results['accuracy_score'] <= 100:
            print("   ✅ Accuracy score is valid")
        else:
            print("   ⚠️  WARNING: Accuracy score out of range")
            
except Exception as e:
    print(f"   ❌ FAIL: Backtest raised exception: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Enhanced Forecast Function  
print("\n3. Testing enhanced forecast generation...")
print("   Testing GARCH volatility and 200 simulations...")

try:
    hist_df, simulations, future_dates = forecast.generate_forecast('AAPL', period=30, num_simulations=200)
    
    print(f"   ✅ PASS: Forecast generated successfully")
    print(f"   Historical data points: {len(hist_df)}")
    print(f"   Simulation shape: {simulations.shape}")
    print(f"   Future dates: {len(future_dates)}")
    
    # Validate
    if simulations.shape[1] == 200:
        print("   ✅ Correct number of simulations (200)")
    else:
        print(f"   ⚠️  WARNING: Expected 200 simulations, got {simulations.shape[1]}")
        
    if len(hist_df) > 365:  # Should have more than 1 year if using 5 years
        print(f"   ✅ Using extended historical data ({len(hist_df)} days)")
    else:
        print(f"   ⚠️  WARNING: Historical data seems short ({len(hist_df)} days)")
        
except Exception as e:
    print(f"   ❌ FAIL: Forecast raised exception: {e}")
    import traceback
    traceback.print_exc()

# Test 4: GARCH Volatility Calculation
print("\n4. Testing GARCH volatility calculation...")

try:
    import pandas as pd
    
    # Create sample returns
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.02, 100))
    
    vols = forecast.calculate_garch_volatility(returns, forecast_days=30)
    
    print(f"   ✅ PASS: GARCH volatility calculated")
    print(f"   Volatility forecast length: {len(vols)}")
    print(f"   Mean volatility: {np.mean(vols):.4f}")
    print(f"   Volatility range: {np.min(vols):.4f} to {np.max(vols):.4f}")
    
    if len(vols) == 30:
        print("   ✅ Correct forecast length")
    else:
        print(f"   ⚠️  WARNING: Expected 30 days, got {len(vols)}")
        
except Exception as e:
    print(f"   ❌ FAIL: GARCH calculation raised exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("All core functionality tests completed.")
print("If all tests passed, the improvements are working correctly!")
print("=" * 60)
