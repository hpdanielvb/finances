import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser && token) {
      setUser(JSON.parse(storedUser));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, message: error.response?.data?.detail || 'Erro no login' };
    }
  };

  const register = async (name, email, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { name, email, password });
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, message: error.response?.data?.detail || 'Erro no cadastro' };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Utility function for Brazilian currency formatting
const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
};

// Utility function for Brazilian date formatting
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('pt-BR');
};

// Login Component
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = isLogin 
      ? await login(formData.email, formData.password)
      : await register(formData.name, formData.email, formData.password);

    if (!result.success) {
      setError(result.message);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">OrçaZenFinanceiro</h1>
          <p className="text-gray-600">Seu controle financeiro pessoal</p>
        </div>

        <div className="flex mb-6">
          <button
            className={`flex-1 py-2 text-center font-medium ${isLogin ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'} rounded-l-lg`}
            onClick={() => setIsLogin(true)}
          >
            Entrar
          </button>
          <button
            className={`flex-1 py-2 text-center font-medium ${!isLogin ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'} rounded-r-lg`}
            onClick={() => setIsLogin(false)}
          >
            Cadastrar
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-medium mb-2">Nome</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
          )}
          
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
          </div>
          
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-medium mb-2">Senha</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Carregando...' : (isLogin ? 'Entrar' : 'Cadastrar')}
          </button>
        </form>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [showReportsModal, setShowReportsModal] = useState(false);
  const [transactionType, setTransactionType] = useState('');
  
  const { user, logout } = useAuth();

  const loadDashboard = async () => {
    try {
      const [summaryRes, accountsRes, transactionsRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary`),
        axios.get(`${API}/accounts`),
        axios.get(`${API}/transactions`),
        axios.get(`${API}/categories`)
      ]);
      
      setSummary(summaryRes.data);
      setAccounts(accountsRes.data);
      setTransactions(transactionsRes.data.slice(0, 5)); // Latest 5 transactions
      setCategories(categoriesRes.data);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // Handle account creation
  const handleCreateAccount = async (accountData) => {
    try {
      await axios.post(`${API}/accounts`, accountData);
      await loadDashboard(); // Refresh data
      setShowAccountModal(false);
      alert('Conta criada com sucesso!');
    } catch (error) {
      alert('Erro ao criar conta: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  // Handle transaction creation
  const handleCreateTransaction = async (transactionData) => {
    try {
      await axios.post(`${API}/transactions`, transactionData);
      await loadDashboard(); // Refresh data
      setShowTransactionModal(false);
      alert('Transação adicionada com sucesso!');
    } catch (error) {
      alert('Erro ao criar transação: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  // Modal handlers
  const openNewAccountModal = () => setShowAccountModal(true);
  const openIncomeModal = () => {
    setTransactionType('Receita');
    setShowTransactionModal(true);
  };
  const openExpenseModal = () => {
    setTransactionType('Despesa');
    setShowTransactionModal(true);
  };
  const openReportsModal = () => setShowReportsModal(true);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">OrçaZenFinanceiro</h1>
              <p className="text-sm text-gray-600">Olá, {user.name}!</p>
            </div>
            <button
              onClick={logout}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Saldo Total</h3>
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(summary?.total_balance || 0)}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Receitas do Mês</h3>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(summary?.monthly_income || 0)}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Despesas do Mês</h3>
            <p className="text-2xl font-bold text-red-600">{formatCurrency(summary?.monthly_expenses || 0)}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Saldo Líquido</h3>
            <p className={`text-2xl font-bold ${(summary?.monthly_net || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(summary?.monthly_net || 0)}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Accounts */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Suas Contas</h2>
            </div>
            <div className="p-6">
              {accounts.length === 0 ? (
                <p className="text-gray-500 text-center">Nenhuma conta cadastrada</p>
              ) : (
                <div className="space-y-4">
                  {accounts.map((account) => (
                    <div key={account.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center">
                        <div 
                          className="w-4 h-4 rounded-full mr-3"
                          style={{ backgroundColor: account.color_hex }}
                        ></div>
                        <div>
                          <p className="font-medium text-gray-900">{account.name}</p>
                          <p className="text-sm text-gray-500">{account.type}</p>
                        </div>
                      </div>
                      <p className="font-bold text-gray-900">{formatCurrency(account.current_balance)}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Transactions */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Transações Recentes</h2>
            </div>
            <div className="p-6">
              {transactions.length === 0 ? (
                <p className="text-gray-500 text-center">Nenhuma transação encontrada</p>
              ) : (
                <div className="space-y-4">
                  {transactions.map((transaction) => (
                    <div key={transaction.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{transaction.description}</p>
                        <p className="text-sm text-gray-500">{formatDate(transaction.transaction_date)}</p>
                      </div>
                      <p className={`font-bold ${transaction.type === 'Receita' ? 'text-green-600' : 'text-red-600'}`}>
                        {transaction.type === 'Receita' ? '+' : '-'}{formatCurrency(transaction.value)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Ações Rápidas</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <button 
                onClick={openNewAccountModal}
                className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Nova Conta
              </button>
              <button 
                onClick={openIncomeModal}
                className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition-colors"
              >
                Adicionar Receita
              </button>
              <button 
                onClick={openExpenseModal}
                className="bg-red-600 text-white px-4 py-3 rounded-lg hover:bg-red-700 transition-colors"
              >
                Adicionar Despesa
              </button>
              <button 
                onClick={openReportsModal}
                className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 transition-colors"
              >
                Ver Relatórios
              </button>
            </div>
          </div>
        </div>

        {/* Account Modal */}
        {showAccountModal && (
          <AccountModal
            onClose={() => setShowAccountModal(false)}
            onCreate={handleCreateAccount}
          />
        )}

        {/* Transaction Modal */}
        {showTransactionModal && (
          <TransactionModal
            type={transactionType}
            accounts={accounts}
            categories={categories}
            onClose={() => setShowTransactionModal(false)}
            onCreate={handleCreateTransaction}
          />
        )}

        {/* Reports Modal */}
        {showReportsModal && (
          <ReportsModal
            summary={summary}
            transactions={transactions}
            accounts={accounts}
            onClose={() => setShowReportsModal(false)}
          />
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="App">
      {user ? <Dashboard /> : <LoginForm />}
    </div>
  );
}

// Account Modal Component
const AccountModal = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'Conta Corrente',
    institution: '',
    initial_balance: 0,
    color_hex: '#4F46E5'
  });

  const accountTypes = [
    'Conta Corrente', 'Poupança', 'Cartão de Crédito', 
    'Investimento', 'Dinheiro em Espécie', 'Outros'
  ];

  const institutions = [
    'Itaú', 'Bradesco', 'Banco do Brasil', 'Caixa Econômica Federal',
    'Santander', 'NuBank', 'C6 Bank', 'Inter', 'PicPay', 'Sicoob',
    'Sicredi', 'Banco Safra', 'XP Investimentos', 'BTG Pactual', 'Outro'
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">Nova Conta</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Nome da Conta</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="Ex: Conta Corrente Principal"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Conta</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
            >
              {accountTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Instituição Financeira</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.institution}
              onChange={(e) => setFormData({...formData, institution: e.target.value})}
            >
              <option value="">Selecione uma instituição</option>
              {institutions.map(institution => (
                <option key={institution} value={institution}>{institution}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Saldo Inicial</label>
            <input
              type="number"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.initial_balance}
              onChange={(e) => setFormData({...formData, initial_balance: parseFloat(e.target.value) || 0})}
              placeholder="0,00"
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Cor da Conta</label>
            <input
              type="color"
              className="w-full h-10 border border-gray-300 rounded-lg"
              value={formData.color_hex}
              onChange={(e) => setFormData({...formData, color_hex: e.target.value})}
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Criar Conta
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Transaction Modal Component
const TransactionModal = ({ type, accounts, categories, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    description: '',
    value: 0,
    type: type,
    transaction_date: new Date().toISOString().split('T')[0],
    account_id: '',
    category_id: '',
    observation: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const transactionData = {
      ...formData,
      transaction_date: new Date(formData.transaction_date).toISOString(),
      value: parseFloat(formData.value)
    };
    onCreate(transactionData);
  };

  const relevantCategories = categories.filter(cat => cat.type === type);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">
          Adicionar {type === 'Receita' ? 'Receita' : 'Despesa'}
        </h3>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Descrição</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder={type === 'Receita' ? 'Ex: Salário' : 'Ex: Supermercado'}
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Valor (R$)</label>
            <input
              type="number"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.value}
              onChange={(e) => setFormData({...formData, value: e.target.value})}
              placeholder="0,00"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Data</label>
            <input
              type="date"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.transaction_date}
              onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Conta</label>
            <select
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.account_id}
              onChange={(e) => setFormData({...formData, account_id: e.target.value})}
            >
              <option value="">Selecione uma conta</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>{account.name}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Categoria</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              value={formData.category_id}
              onChange={(e) => setFormData({...formData, category_id: e.target.value})}
            >
              <option value="">Selecione uma categoria</option>
              {relevantCategories.map(category => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Observação (opcional)</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              rows="2"
              value={formData.observation}
              onChange={(e) => setFormData({...formData, observation: e.target.value})}
              placeholder="Observações adicionais..."
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={`px-4 py-2 text-white rounded-lg ${
                type === 'Receita' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              Adicionar {type}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Reports Modal Component
const ReportsModal = ({ summary, transactions, accounts, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold">Relatórios Financeiros</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Summary Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-800 mb-2">Saldo Total</h4>
            <p className="text-2xl font-bold text-blue-900">
              {formatCurrency(summary?.total_balance || 0)}
            </p>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-medium text-green-800 mb-2">Receitas do Mês</h4>
            <p className="text-2xl font-bold text-green-900">
              {formatCurrency(summary?.monthly_income || 0)}
            </p>
          </div>
          
          <div className="bg-red-50 p-4 rounded-lg">
            <h4 className="font-medium text-red-800 mb-2">Despesas do Mês</h4>
            <p className="text-2xl font-bold text-red-900">
              {formatCurrency(summary?.monthly_expenses || 0)}
            </p>
          </div>
        </div>

        {/* Accounts Section */}
        <div className="mb-8">
          <h4 className="text-lg font-semibold mb-4">Resumo por Conta</h4>
          <div className="space-y-3">
            {accounts.map(account => (
              <div key={account.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div 
                    className="w-4 h-4 rounded-full mr-3"
                    style={{ backgroundColor: account.color_hex }}
                  ></div>
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <p className="text-sm text-gray-500">{account.type} - {account.institution}</p>
                  </div>
                </div>
                <p className="font-bold text-lg">{formatCurrency(account.current_balance)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Transactions */}
        <div>
          <h4 className="text-lg font-semibold mb-4">Transações Recentes</h4>
          <div className="space-y-2">
            {transactions.map(transaction => (
              <div key={transaction.id} className="flex justify-between items-center p-3 border rounded-lg">
                <div>
                  <p className="font-medium">{transaction.description}</p>
                  <p className="text-sm text-gray-500">
                    {formatDate(transaction.transaction_date)} • {transaction.type}
                  </p>
                </div>
                <p className={`font-bold ${
                  transaction.type === 'Receita' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {transaction.type === 'Receita' ? '+' : '-'}{formatCurrency(transaction.value)}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};

function AppWrapper() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWrapper;