// =====================================================================
// COMPLETE REACT FRONTEND - Progressive Data Collection
// =====================================================================
// Ready-to-use React components for retirement goal onboarding
// =====================================================================

// =====================================================================
// 1. OnboardingForm.jsx - Minimal Registration (3-minute setup)
// =====================================================================

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './OnboardingForm.css';

const OnboardingForm = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    phone: '',
    current_age: '',
    desired_retirement_age: '',
    marital_status: 'single',
    number_of_dependents: 0,
    monthly_income: '',
    monthly_expense: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateStep = () => {
    const newErrors = {};

    if (step === 1) {
      if (!formData.email) newErrors.email = 'Email is required';
      else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Invalid email';
      if (!formData.full_name) newErrors.full_name = 'Name is required';
    }

    if (step === 2) {
      if (!formData.current_age || formData.current_age < 18 || formData.current_age > 100) {
        newErrors.current_age = 'Age must be between 18 and 100';
      }
      if (!formData.desired_retirement_age || formData.desired_retirement_age <= formData.current_age) {
        newErrors.desired_retirement_age = 'Retirement age must be greater than current age';
      }
    }

    if (step === 3) {
      if (!formData.monthly_income || formData.monthly_income <= 0) {
        newErrors.monthly_income = 'Income must be greater than 0';
      }
      if (!formData.monthly_expense || formData.monthly_expense <= 0) {
        newErrors.monthly_expense = 'Expense must be greater than 0';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep()) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateStep()) return;

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/onboarding/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          full_name: formData.full_name,
          phone: formData.phone || null,
          current_age: parseInt(formData.current_age),
          desired_retirement_age: parseInt(formData.desired_retirement_age),
          marital_status: formData.marital_status,
          number_of_dependents: parseInt(formData.number_of_dependents),
          monthly_income: parseFloat(formData.monthly_income),
          monthly_expense: parseFloat(formData.monthly_expense)
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Success! Show enhancement dialog
        const shouldEnhance = window.confirm(
          '✅ Account created successfully!\n\n' +
          'Would you like to add retirement assets and loans for better accuracy?\n' +
          '(Takes only 2-3 minutes)'
        );

        if (shouldEnhance) {
          navigate(`/add-assets/${result.user.user_id}`);
        } else {
          navigate(`/dashboard/${result.user.user_id}`);
        }
      } else {
        setErrors({ submit: result.detail || 'Registration failed' });
      }
    } catch (error) {
      console.error('Error:', error);
      setErrors({ submit: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="form-step">
      <h2>Let's Get Started</h2>
      <p>Tell us about yourself</p>

      <div className="form-group">
        <label>Email *</label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="you@example.com"
          className={errors.email ? 'error' : ''}
        />
        {errors.email && <span className="error-text">{errors.email}</span>}
      </div>

      <div className="form-group">
        <label>Full Name *</label>
        <input
          type="text"
          name="full_name"
          value={formData.full_name}
          onChange={handleChange}
          placeholder="John Doe"
          className={errors.full_name ? 'error' : ''}
        />
        {errors.full_name && <span className="error-text">{errors.full_name}</span>}
      </div>

      <div className="form-group">
        <label>Phone (Optional)</label>
        <input
          type="tel"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="+91 9876543210"
        />
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="form-step">
      <h2>Your Retirement Goals</h2>

      <div className="form-group">
        <label>Current Age *</label>
        <input
          type="number"
          name="current_age"
          value={formData.current_age}
          onChange={handleChange}
          placeholder="32"
          min="18"
          max="100"
          className={errors.current_age ? 'error' : ''}
        />
        {errors.current_age && <span className="error-text">{errors.current_age}</span>}
      </div>

      <div className="form-group">
        <label>Desired Retirement Age *</label>
        <input
          type="number"
          name="desired_retirement_age"
          value={formData.desired_retirement_age}
          onChange={handleChange}
          placeholder="60"
          min={parseInt(formData.current_age) + 1 || 18}
          max="75"
          className={errors.desired_retirement_age ? 'error' : ''}
        />
        {errors.desired_retirement_age && <span className="error-text">{errors.desired_retirement_age}</span>}
      </div>

      <div className="form-group">
        <label>Marital Status *</label>
        <select
          name="marital_status"
          value={formData.marital_status}
          onChange={handleChange}
        >
          <option value="single">Single</option>
          <option value="married">Married</option>
          <option value="divorced">Divorced</option>
          <option value="widowed">Widowed</option>
        </select>
      </div>

      <div className="form-group">
        <label>Number of Dependents</label>
        <input
          type="number"
          name="number_of_dependents"
          value={formData.number_of_dependents}
          onChange={handleChange}
          min="0"
          max="10"
        />
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="form-step">
      <h2>Monthly Finances</h2>

      <div className="form-group">
        <label>Monthly Household Income *</label>
        <div className="input-with-prefix">
          <span className="prefix">₹</span>
          <input
            type="number"
            name="monthly_income"
            value={formData.monthly_income}
            onChange={handleChange}
            placeholder="80000"
            min="0"
            className={errors.monthly_income ? 'error' : ''}
          />
        </div>
        {errors.monthly_income && <span className="error-text">{errors.monthly_income}</span>}
        <small>Include salary, business income, rental income, etc.</small>
      </div>

      <div className="form-group">
        <label>Monthly Household Expenses *</label>
        <div className="input-with-prefix">
          <span className="prefix">₹</span>
          <input
            type="number"
            name="monthly_expense"
            value={formData.monthly_expense}
            onChange={handleChange}
            placeholder="50000"
            min="0"
            className={errors.monthly_expense ? 'error' : ''}
          />
        </div>
        {errors.monthly_expense && <span className="error-text">{errors.monthly_expense}</span>}
        <small>Include rent, groceries, utilities, entertainment, etc.</small>
      </div>

      {formData.monthly_income && formData.monthly_expense && (
        <div className="summary-box">
          <p>Monthly Surplus: ₹{(formData.monthly_income - formData.monthly_expense).toLocaleString()}</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="onboarding-container">
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${(step / 3) * 100}%` }}></div>
      </div>

      <div className="onboarding-form">
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}

        {errors.submit && (
          <div className="error-banner">{errors.submit}</div>
        )}

        <div className="button-group">
          {step > 1 && (
            <button type="button" onClick={handleBack} className="btn-secondary">
              Back
            </button>
          )}
          
          {step < 3 ? (
            <button type="button" onClick={handleNext} className="btn-primary">
              Continue
            </button>
          ) : (
            <button 
              type="button" 
              onClick={handleSubmit} 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Complete Setup'}
            </button>
          )}
        </div>

        <div className="step-indicator">
          Step {step} of 3
        </div>
      </div>
    </div>
  );
};

export default OnboardingForm;


// =====================================================================
// 2. AddAssets.jsx - Collect Retirement Assets
// =====================================================================

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './AddAssets.css';

const AddAssets = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [hasAssets, setHasAssets] = useState(null);
  const [assets, setAssets] = useState([{
    asset_type: 'epf',
    asset_name: '',
    current_value: '',
    monthly_contribution: ''
  }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const assetTypes = [
    { value: 'epf', label: 'EPF (Employee Provident Fund)', placeholder: 'My EPF Account' },
    { value: 'ppf', label: 'PPF (Public Provident Fund)', placeholder: 'My PPF Account' },
    { value: 'nps', label: 'NPS (National Pension System)', placeholder: 'My NPS Account' },
    { value: 'mutual_fund', label: 'Mutual Funds', placeholder: 'e.g., SBI Equity Fund' },
    { value: 'stocks', label: 'Stocks', placeholder: 'Stock Portfolio' },
    { value: 'fd', label: 'Fixed Deposits', placeholder: 'Bank FD' },
    { value: 'other', label: 'Other Retirement Savings', placeholder: 'Other Savings' }
  ];

  const addAsset = () => {
    setAssets([...assets, {
      asset_type: 'epf',
      asset_name: '',
      current_value: '',
      monthly_contribution: ''
    }]);
  };

  const removeAsset = (index) => {
    if (assets.length > 1) {
      const updated = assets.filter((_, i) => i !== index);
      setAssets(updated);
    }
  };

  const updateAsset = (index, field, value) => {
    const updated = [...assets];
    updated[index][field] = value;
    setAssets(updated);
  };

  const getPlaceholder = (type) => {
    const asset = assetTypes.find(a => a.value === type);
    return asset ? asset.placeholder : 'Asset Name';
  };

  const handleSubmit = async () => {
    if (hasAssets === false) {
      // User has no assets, skip to next
      navigate(`/add-loans/${userId}`);
      return;
    }

    // Validate
    const invalid = assets.some(a => 
      !a.asset_name || !a.current_value || parseFloat(a.current_value) <= 0
    );

    if (invalid) {
      setError('Please fill all required fields with valid values');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/onboarding/assets/${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            assets: assets.map(a => ({
              asset_type: a.asset_type,
              asset_name: a.asset_name,
              current_value: parseFloat(a.current_value),
              monthly_contribution: parseFloat(a.monthly_contribution) || 0
            }))
          })
        }
      );

      const result = await response.json();

      if (response.ok && result.success) {
        // Success! Move to loans
        navigate(`/add-loans/${userId}`);
      } else {
        setError(result.detail || 'Failed to save assets');
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-assets-container">
      <div className="header">
        <h1>Add Retirement Assets</h1>
        <p>Optional - This helps us give you accurate projections</p>
      </div>

      <div className="question-box">
        <h3>Do you have any retirement savings?</h3>
        <div className="button-group">
          <button
            className={`option-btn ${hasAssets === true ? 'active' : ''}`}
            onClick={() => setHasAssets(true)}
          >
            Yes, I do
          </button>
          <button
            className={`option-btn ${hasAssets === false ? 'active' : ''}`}
            onClick={() => setHasAssets(false)}
          >
            No, not yet
          </button>
        </div>
      </div>

      {hasAssets === true && (
        <div className="assets-section">
          <div className="benefit-box">
            <h4>💡 Why add assets?</h4>
            <ul>
              <li>✅ Get accurate retirement projections</li>
              <li>✅ See exactly when your money runs out</li>
              <li>✅ Get personalized recommendations</li>
            </ul>
          </div>

          {assets.map((asset, index) => (
            <div key={index} className="asset-card">
              <div className="card-header">
                <h4>Asset {index + 1}</h4>
                {assets.length > 1 && (
                  <button
                    onClick={() => removeAsset(index)}
                    className="remove-btn"
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="form-group">
                <label>Asset Type *</label>
                <select
                  value={asset.asset_type}
                  onChange={(e) => updateAsset(index, 'asset_type', e.target.value)}
                >
                  {assetTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Asset Name *</label>
                <input
                  type="text"
                  value={asset.asset_name}
                  onChange={(e) => updateAsset(index, 'asset_name', e.target.value)}
                  placeholder={getPlaceholder(asset.asset_type)}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Current Value * (₹)</label>
                  <input
                    type="number"
                    value={asset.current_value}
                    onChange={(e) => updateAsset(index, 'current_value', e.target.value)}
                    placeholder="350000"
                    min="0"
                  />
                </div>

                <div className="form-group">
                  <label>Monthly Contribution (₹)</label>
                  <input
                    type="number"
                    value={asset.monthly_contribution}
                    onChange={(e) => updateAsset(index, 'monthly_contribution', e.target.value)}
                    placeholder="12000"
                    min="0"
                  />
                  <small>Optional - How much you add monthly</small>
                </div>
              </div>
            </div>
          ))}

          <button onClick={addAsset} className="add-more-btn">
            + Add Another Asset
          </button>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      <div className="action-buttons">
        <button
          onClick={() => navigate(`/add-loans/${userId}`)}
          className="btn-secondary"
        >
          Skip for Now
        </button>
        <button
          onClick={handleSubmit}
          className="btn-primary"
          disabled={loading}
        >
          {loading ? 'Saving...' : hasAssets ? 'Save & Continue' : 'Continue'}
        </button>
      </div>

      <div className="progress-text">
        Step 2 of 3 - Add retirement savings
      </div>
    </div>
  );
};

export default AddAssets;


// =====================================================================
// 3. AddLoans.jsx - Collect Current Loans
// =====================================================================

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './AddLoans.css';

const AddLoans = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [hasLoans, setHasLoans] = useState(null);
  const [loans, setLoans] = useState([{
    loan_type: 'home',
    principal_amount: '',
    outstanding_balance: '',
    monthly_emi: '',
    interest_rate: '',
    start_date: '',
    end_date: ''
  }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loanTypes = [
    { value: 'home', label: 'Home Loan' },
    { value: 'vehicle', label: 'Vehicle Loan' },
    { value: 'personal', label: 'Personal Loan' },
    { value: 'education', label: 'Education Loan' },
    { value: 'other', label: 'Other Loan' }
  ];

  const addLoan = () => {
    setLoans([...loans, {
      loan_type: 'home',
      principal_amount: '',
      outstanding_balance: '',
      monthly_emi: '',
      interest_rate: '',
      start_date: '',
      end_date: ''
    }]);
  };

  const removeLoan = (index) => {
    if (loans.length > 1) {
      const updated = loans.filter((_, i) => i !== index);
      setLoans(updated);
    }
  };

  const updateLoan = (index, field, value) => {
    const updated = [...loans];
    updated[index][field] = value;
    setLoans(updated);
  };

  const handleSubmit = async () => {
    if (hasLoans === false) {
      // User has no loans, go to dashboard
      navigate(`/dashboard/${userId}`);
      return;
    }

    // Validate
    const invalid = loans.some(l => 
      !l.principal_amount || !l.outstanding_balance || 
      !l.monthly_emi || !l.interest_rate || 
      !l.start_date || !l.end_date
    );

    if (invalid) {
      setError('Please fill all required fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/onboarding/loans/${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            loans: loans.map(l => ({
              loan_type: l.loan_type,
              principal_amount: parseFloat(l.principal_amount),
              outstanding_balance: parseFloat(l.outstanding_balance),
              monthly_emi: parseFloat(l.monthly_emi),
              interest_rate: parseFloat(l.interest_rate),
              start_date: l.start_date,
              end_date: l.end_date
            }))
          })
        }
      );

      const result = await response.json();

      if (response.ok && result.success) {
        // Success! Go to dashboard
        navigate(`/dashboard/${userId}`);
      } else {
        setError(result.detail || 'Failed to save loans');
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-loans-container">
      <div className="header">
        <h1>Add Current Loans</h1>
        <p>Optional - Helps us plan your debt-free retirement</p>
      </div>

      <div className="question-box">
        <h3>Do you have any active loans?</h3>
        <div className="button-group">
          <button
            className={`option-btn ${hasLoans === true ? 'active' : ''}`}
            onClick={() => setHasLoans(true)}
          >
            Yes, I do
          </button>
          <button
            className={`option-btn ${hasLoans === false ? 'active' : ''}`}
            onClick={() => setHasLoans(false)}
          >
            No loans
          </button>
        </div>
      </div>

      {hasLoans === true && (
        <div className="loans-section">
          {loans.map((loan, index) => (
            <div key={index} className="loan-card">
              <div className="card-header">
                <h4>Loan {index + 1}</h4>
                {loans.length > 1 && (
                  <button
                    onClick={() => removeLoan(index)}
                    className="remove-btn"
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="form-group">
                <label>Loan Type *</label>
                <select
                  value={loan.loan_type}
                  onChange={(e) => updateLoan(index, 'loan_type', e.target.value)}
                >
                  {loanTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Original Amount * (₹)</label>
                  <input
                    type="number"
                    value={loan.principal_amount}
                    onChange={(e) => updateLoan(index, 'principal_amount', e.target.value)}
                    placeholder="3500000"
                    min="0"
                  />
                </div>

                <div className="form-group">
                  <label>Outstanding * (₹)</label>
                  <input
                    type="number"
                    value={loan.outstanding_balance}
                    onChange={(e) => updateLoan(index, 'outstanding_balance', e.target.value)}
                    placeholder="3200000"
                    min="0"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Monthly EMI * (₹)</label>
                  <input
                    type="number"
                    value={loan.monthly_emi}
                    onChange={(e) => updateLoan(index, 'monthly_emi', e.target.value)}
                    placeholder="30000"
                    min="0"
                  />
                </div>

                <div className="form-group">
                  <label>Interest Rate * (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={loan.interest_rate}
                    onChange={(e) => updateLoan(index, 'interest_rate', e.target.value)}
                    placeholder="8.5"
                    min="0"
                    max="100"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Start Date *</label>
                  <input
                    type="date"
                    value={loan.start_date}
                    onChange={(e) => updateLoan(index, 'start_date', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>End Date *</label>
                  <input
                    type="date"
                    value={loan.end_date}
                    onChange={(e) => updateLoan(index, 'end_date', e.target.value)}
                  />
                </div>
              </div>
            </div>
          ))}

          <button onClick={addLoan} className="add-more-btn">
            + Add Another Loan
          </button>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      <div className="action-buttons">
        <button
          onClick={() => navigate(`/dashboard/${userId}`)}
          className="btn-secondary"
        >
          Skip for Now
        </button>
        <button
          onClick={handleSubmit}
          className="btn-primary"
          disabled={loading}
        >
          {loading ? 'Saving...' : 'Go to Dashboard'}
        </button>
      </div>

      <div className="progress-text">
        Step 3 of 3 - Add current loans
      </div>
    </div>
  );
};

export default AddLoans;


// =====================================================================
// 4. Dashboard.jsx - Show Financial Snapshot & Enhancement Prompts
// =====================================================================

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [snapshot, setSnapshot] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, [userId]);

  const fetchData = async () => {
    try {
      // Fetch snapshot
      const snapshotRes = await fetch(
        `http://localhost:8000/api/v1/onboarding/snapshot/${userId}`
      );
      const snapshotData = await snapshotRes.json();

      // Fetch status
      const statusRes = await fetch(
        `http://localhost:8000/api/v1/onboarding/status/${userId}`
      );
      const statusData = await statusRes.json();

      if (snapshotRes.ok && statusRes.ok) {
        setSnapshot(snapshotData.data);
        setStatus(statusData.data);
      } else {
        setError('Failed to load data');
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading your dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  const yearsToRetirement = snapshot.desired_retirement_age - snapshot.current_age;
  const monthlySurplus = snapshot.monthly_income - snapshot.monthly_household_expense - (snapshot.total_monthly_emi || 0);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Welcome, {snapshot.full_name}! 👋</h1>
        <p>Your retirement planning dashboard</p>
      </header>

      {/* Readiness Score */}
      <div className="readiness-card">
        <h2>Profile Completion</h2>
        <div className="readiness-score">
          <div className="score-circle">
            <span className="percentage">{Math.round(status.overall_percentage)}%</span>
          </div>
          <div className="score-details">
            <p>Required Steps: {status.required.completed}/{status.required.total} ✅</p>
            <p>Optional Steps: {status.optional.completed}/{status.optional.total}</p>
          </div>
        </div>
      </div>

      {/* Financial Snapshot */}
      <div className="snapshot-section">
        <h2>Your Financial Snapshot</h2>
        
        <div className="stats-grid">
          <div className="stat-card">
            <span className="label">Current Age</span>
            <span className="value">{snapshot.current_age} years</span>
          </div>
          
          <div className="stat-card">
            <span className="label">Retirement Age</span>
            <span className="value">{snapshot.desired_retirement_age} years</span>
          </div>
          
          <div className="stat-card">
            <span className="label">Years to Retirement</span>
            <span className="value highlight">{yearsToRetirement} years</span>
          </div>
          
          <div className="stat-card">
            <span className="label">Monthly Income</span>
            <span className="value">₹{snapshot.monthly_income?.toLocaleString()}</span>
          </div>
          
          <div className="stat-card">
            <span className="label">Monthly Expenses</span>
            <span className="value">₹{snapshot.monthly_household_expense?.toLocaleString()}</span>
          </div>
          
          <div className="stat-card">
            <span className="label">Monthly EMI</span>
            <span className="value">₹{(snapshot.total_monthly_emi || 0).toLocaleString()}</span>
          </div>
          
          <div className="stat-card">
            <span className="label">Monthly Surplus</span>
            <span className={`value ${monthlySurplus < 0 ? 'negative' : 'positive'}`}>
              ₹{monthlySurplus.toLocaleString()}
            </span>
          </div>
          
          <div className="stat-card highlight-card">
            <span className="label">Total Retirement Savings</span>
            <span className="value">₹{(snapshot.total_retirement_savings || 0).toLocaleString()}</span>
          </div>
          
          <div className="stat-card highlight-card">
            <span className="label">Monthly Retirement Contribution</span>
            <span className="value">₹{(snapshot.total_monthly_contribution || 0).toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Enhancement Prompts */}
      {(!status.optional.steps.has_assets || !status.optional.steps.has_loans) && (
        <div className="enhancement-section">
          <h2>⚡ Enhance Your Plan</h2>
          <p>Add more details for accurate retirement projections</p>

          <div className="enhancement-cards">
            {!status.optional.steps.has_assets && (
              <div className="enhancement-card">
                <div className="icon">💰</div>
                <h3>Add Retirement Assets</h3>
                <p>Add your EPF, PPF, mutual funds, etc.</p>
                <ul>
                  <li>✅ Get accurate projections</li>
                  <li>✅ See when money runs out</li>
                  <li>✅ Get personalized tips</li>
                </ul>
                <button
                  onClick={() => navigate(`/add-assets/${userId}`)}
                  className="btn-primary"
                >
                  Add Assets (2 min)
                </button>
              </div>
            )}

            {!status.optional.steps.has_loans && (
              <div className="enhancement-card">
                <div className="icon">🏠</div>
                <h3>Add Current Loans</h3>
                <p>Add your home loan, vehicle loan, etc.</p>
                <ul>
                  <li>✅ Plan debt-free retirement</li>
                  <li>✅ Optimize loan payments</li>
                  <li>✅ Better cash flow planning</li>
                </ul>
                <button
                  onClick={() => navigate(`/add-loans/${userId}`)}
                  className="btn-primary"
                >
                  Add Loans (2 min)
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Next Steps Section */}
      <div className="next-steps-section">
        <h2>🎯 Next: Build Retirement Engine</h2>
        <div className="next-steps-card">
          <p>Now that you have the data, you need to:</p>
          <ol>
            <li>Calculate retirement corpus required</li>
            <li>Project future value of current savings</li>
            <li>Calculate gap (surplus or shortfall)</li>
            <li>Determine how long money will last</li>
            <li>Generate action recommendations</li>
          </ol>
          <p className="note">
            <strong>Note:</strong> This requires implementing a retirement calculation engine.
            See the Retirement Engine Guide for details.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;


// =====================================================================
// 5. App.jsx - Router Configuration
// =====================================================================

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import OnboardingForm from './components/OnboardingForm';
import AddAssets from './components/AddAssets';
import AddLoans from './components/AddLoans';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<OnboardingForm />} />
          <Route path="/add-assets/:userId" element={<AddAssets />} />
          <Route path="/add-loans/:userId" element={<AddLoans />} />
          <Route path="/dashboard/:userId" element={<Dashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;


// =====================================================================
// INSTALLATION INSTRUCTIONS
// =====================================================================

/*
1. Create React App:
   npx create-react-app retirement-frontend
   cd retirement-frontend

2. Install dependencies:
   npm install react-router-dom

3. Copy components:
   - Create src/components/ folder
   - Copy OnboardingForm.jsx, AddAssets.jsx, AddLoans.jsx, Dashboard.jsx
   - Replace src/App.jsx with the App.jsx code above

4. Add CSS files (create matching .css files for each component)

5. Start development server:
   npm start

6. Make sure FastAPI backend is running:
   cd ../retirement_api
   uvicorn main:app --reload

7. Test the flow:
   - Go to http://localhost:3000
   - Complete onboarding
   - Add assets
   - Add loans
   - See dashboard
*/
