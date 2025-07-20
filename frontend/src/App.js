import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";
import { Toaster, toast } from 'react-hot-toast';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Plus, TrendingUp, TrendingDown, CreditCard, PiggyBank, DollarSign, FileText, Settings, Bell, Calendar, Filter, Download, Upload, Edit, Trash2, Eye, EyeOff } from 'lucide-react';
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Enhanced Auth Context with better session management
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
    const storedToken = localStorage.getItem('token');
    
    if (storedUser && storedToken) {
      try {
        setUser(JSON.parse(storedUser));
        setToken(storedToken);
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        console.log('User restored from localStorage:', JSON.parse(storedUser));
      } catch (error) {
        console.error('Error parsing stored user:', error);
        logout();
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      console.log('Login successful:', user);
      toast.success(`Bem-vindo, ${user.name}!`);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, message: error.response?.data?.detail || 'Erro no login' };
    }
  };

  const register = async (name, email, password, confirmPassword) => {
    try {
      const response = await axios.post(`${API}/auth/register`, { 
        name, email, password, confirm_password: confirmPassword 
      });
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      console.log('Registration successful:', user);
      toast.success(`Conta criada com sucesso! Bem-vindo, ${user.name}!`);
      
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, message: error.response?.data?.detail || 'Erro no cadastro' };
    }
  };

  const logout = () => {
    console.log('Logging out user');
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    toast.success('Logout realizado com sucesso!');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Utility functions
const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value || 0);
};

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('pt-BR');
};

const formatDateForInput = (date) => {
  return new Date(date).toISOString().split('T')[0];
};

// Enhanced Login Component
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ 
    name: '', email: '', password: '', confirmPassword: '' 
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (!isLogin && formData.password !== formData.confirmPassword) {
        setError('Senhas não coincidem');
        setLoading(false);
        return;
      }

      const result = isLogin 
        ? await login(formData.email, formData.password)
        : await register(formData.name, formData.email, formData.password, formData.confirmPassword);

      if (!result.success) {
        setError(result.message);
        toast.error(result.message);
      }
      // Don't set loading to false here - let the context handle the redirect
    } catch (error) {
      console.error('Form submit error:', error);
      setError('Erro interno. Tente novamente.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            <h1 className="text-4xl font-bold mb-2">OrçaZenFinanceiro</h1>
          </div>
          <p className="text-gray-600">Seu controle financeiro pessoal completo</p>
        </div>

        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button
            className={`flex-1 py-2 text-center font-medium transition-all ${
              isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
            } rounded-md`}
            onClick={() => setIsLogin(true)}
          >
            Entrar
          </button>
          <button
            className={`flex-1 py-2 text-center font-medium transition-all ${
              !isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
            } rounded-md`}
            onClick={() => setIsLogin(false)}
          >
            Cadastrar
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">Nome Completo</label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Digite seu nome completo"
                required
              />
            </div>
          )}
          
          <div>
            <label className="block text-gray-700 text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              placeholder="seu@email.com"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-700 text-sm font-medium mb-2">Senha</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all pr-12"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Sua senha"
                required
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">Confirmar Senha</label>
              <input
                type="password"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                placeholder="Confirme sua senha"
                required
              />
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg transition-all shadow-lg hover:shadow-xl"
          >
            {loading ? 'Carregando...' : (isLogin ? 'Entrar' : 'Criar Conta')}
          </button>
        </form>

        {isLogin && (
          <div className="text-center mt-4">
            <button className="text-blue-600 hover:text-blue-800 text-sm">
              Esqueci minha senha
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Dashboard Component
const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('dashboard');
  
  // Modal states
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [showReportsModal, setShowReportsModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transactionType, setTransactionType] = useState('');
  const [editingItem, setEditingItem] = useState(null);

  const { user, logout } = useAuth();

  const loadDashboard = async () => {
    try {
      const [summaryRes, accountsRes, transactionsRes, categoriesRes, budgetsRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary`),
        axios.get(`${API}/accounts`),
        axios.get(`${API}/transactions?limit=10`),
        axios.get(`${API}/categories`),
        axios.get(`${API}/budgets`)
      ]);
      
      setSummary(summaryRes.data);
      setAccounts(accountsRes.data);
      setTransactions(transactionsRes.data);
      setCategories(categoriesRes.data);
      setBudgets(budgetsRes.data);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      
      // Only logout if it's an authentication error, not network errors
      if (error.response?.status === 401 && error.response?.data?.detail?.includes('inválido')) {
        toast.error('Sessão expirada. Faça login novamente.');
        logout();
      } else {
        toast.error('Erro ao carregar dados. Tente novamente.');
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // Event handlers
  const handleCreateAccount = async (accountData) => {
    try {
      await axios.post(`${API}/accounts`, accountData);
      await loadDashboard();
      setShowAccountModal(false);
      setEditingItem(null);
      toast.success('Conta criada com sucesso!');
    } catch (error) {
      toast.error('Erro ao criar conta: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleCreateTransaction = async (transactionData) => {
    try {
      await axios.post(`${API}/transactions`, transactionData);
      await loadDashboard();
      setShowTransactionModal(false);
      setEditingItem(null);
      toast.success('Transação adicionada com sucesso!');
    } catch (error) {
      toast.error('Erro ao criar transação: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleCreateTransfer = async (transferData) => {
    try {
      await axios.post(`${API}/transfers`, transferData);
      await loadDashboard();
      setShowTransferModal(false);
      toast.success('Transferência realizada com sucesso!');
    } catch (error) {
      toast.error('Erro ao realizar transferência: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleCreateBudget = async (budgetData) => {
    try {
      await axios.post(`${API}/budgets`, budgetData);
      await loadDashboard();
      setShowBudgetModal(false);
      toast.success('Orçamento definido com sucesso!');
    } catch (error) {
      toast.error('Erro ao definir orçamento: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  // Modal handlers
  const openNewAccountModal = () => {
    setEditingItem(null);
    setShowAccountModal(true);
  };
  
  const openIncomeModal = () => {
    setEditingItem(null);
    setTransactionType('Receita');
    setShowTransactionModal(true);
  };
  
  const openExpenseModal = () => {
    setEditingItem(null);
    setTransactionType('Despesa');
    setShowTransactionModal(true);
  };
  
  const openTransferModal = () => setShowTransferModal(true);
  const openBudgetModal = () => setShowBudgetModal(true);
  const openReportsModal = () => setShowReportsModal(true);

  // Chart colors
  const COLORS = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

  // Prepare chart data
  const expenseChartData = summary?.expense_by_category ? 
    Object.entries(summary.expense_by_category).map(([name, value], index) => ({
      name,
      value,
      color: COLORS[index % COLORS.length]
    })) : [];

  const incomeChartData = summary?.income_by_category ? 
    Object.entries(summary.income_by_category).map(([name, value], index) => ({
      name,
      value,
      color: COLORS[index % COLORS.length]
    })) : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">Carregando seu painel financeiro...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Enhanced Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                <h1 className="text-2xl font-bold">OrçaZenFinanceiro</h1>
              </div>
              <div className="hidden md:flex space-x-1">
                <button
                  onClick={() => setActiveView('dashboard')}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    activeView === 'dashboard' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => setActiveView('transactions')}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    activeView === 'transactions' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Transações
                </button>
                <button
                  onClick={() => setActiveView('accounts')}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    activeView === 'accounts' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Contas
                </button>
                <button
                  onClick={() => setActiveView('budgets')}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    activeView === 'budgets' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Orçamentos
                </button>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm text-gray-600">Bem-vindo,</p>
                <p className="font-medium text-gray-900">{user.name}</p>
              </div>
              
              <button className="p-2 text-gray-400 hover:text-gray-600 relative">
                <Bell size={20} />
                {summary?.pending_transactions?.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {summary.pending_transactions.length}
                  </span>
                )}
              </button>
              
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeView === 'dashboard' && (
          <>
            {/* Enhanced Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm font-medium">Saldo Total</p>
                    <p className="text-2xl font-bold">{formatCurrency(summary?.total_balance || 0)}</p>
                  </div>
                  <PiggyBank className="w-8 h-8 text-blue-200" />
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100 text-sm font-medium">Receitas do Mês</p>
                    <p className="text-2xl font-bold">{formatCurrency(summary?.monthly_income || 0)}</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-200" />
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-red-500 to-red-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-red-100 text-sm font-medium">Despesas do Mês</p>
                    <p className="text-2xl font-bold">{formatCurrency(summary?.monthly_expenses || 0)}</p>
                  </div>
                  <TrendingDown className="w-8 h-8 text-red-200" />
                </div>
              </div>
              
              <div className={`bg-gradient-to-r rounded-xl shadow-lg p-6 text-white ${
                (summary?.monthly_net || 0) >= 0 ? 'from-emerald-500 to-emerald-600' : 'from-orange-500 to-orange-600'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white text-sm font-medium opacity-90">Saldo Líquido</p>
                    <p className="text-2xl font-bold">{formatCurrency(summary?.monthly_net || 0)}</p>
                  </div>
                  <DollarSign className="w-8 h-8 text-white opacity-75" />
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Expense Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Despesas por Categoria</h3>
                {expenseChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={expenseChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        dataKey="value"
                      >
                        {expenseChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">
                    Nenhuma despesa encontrada neste mês
                  </div>
                )}
              </div>

              {/* Income Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Receitas por Categoria</h3>
                {incomeChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={incomeChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        dataKey="value"
                      >
                        {incomeChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">
                    Nenhuma receita encontrada neste mês
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Accounts */}
              <div className="bg-white rounded-xl shadow-lg">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900">Suas Contas</h2>
                  <button
                    onClick={openNewAccountModal}
                    className="text-blue-600 hover:text-blue-800 font-medium text-sm flex items-center gap-1"
                  >
                    <Plus size={16} />
                    Nova Conta
                  </button>
                </div>
                <div className="p-6">
                  {accounts.length === 0 ? (
                    <div className="text-center py-8">
                      <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-gray-500">Nenhuma conta cadastrada</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {accounts.map((account) => (
                        <div key={account.id} className="flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50 transition-colors">
                          <div className="flex items-center">
                            <div 
                              className="w-4 h-4 rounded-full mr-3 shadow-sm"
                              style={{ backgroundColor: account.color_hex }}
                            ></div>
                            <div>
                              <p className="font-medium text-gray-900">{account.name}</p>
                              <p className="text-sm text-gray-500">{account.type} • {account.institution}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-gray-900">{formatCurrency(account.current_balance)}</p>
                            <p className="text-xs text-gray-500">Saldo atual</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Recent Transactions */}
              <div className="bg-white rounded-xl shadow-lg">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900">Transações Recentes</h2>
                  <button
                    onClick={() => setActiveView('transactions')}
                    className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                  >
                    Ver todas
                  </button>
                </div>
                <div className="p-6">
                  {transactions.length === 0 ? (
                    <div className="text-center py-8">
                      <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-gray-500">Nenhuma transação encontrada</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {transactions.slice(0, 5).map((transaction) => (
                        <div key={transaction.id} className="flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50 transition-colors">
                          <div className="flex items-center">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-3 ${
                              transaction.type === 'Receita' ? 'bg-green-100' : 'bg-red-100'
                            }`}>
                              {transaction.type === 'Receita' ? 
                                <TrendingUp className="w-5 h-5 text-green-600" /> : 
                                <TrendingDown className="w-5 h-5 text-red-600" />
                              }
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{transaction.description}</p>
                              <p className="text-sm text-gray-500">{formatDate(transaction.transaction_date)}</p>
                            </div>
                          </div>
                          <p className={`font-bold ${
                            transaction.type === 'Receita' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {transaction.type === 'Receita' ? '+' : '-'}{formatCurrency(transaction.value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Actions - Enhanced */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Ações Rápidas</h2>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <button 
                  onClick={openNewAccountModal}
                  className="flex flex-col items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors group"
                >
                  <CreditCard className="w-8 h-8 text-blue-600 mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium text-blue-900">Nova Conta</span>
                </button>
                
                <button 
                  onClick={openIncomeModal}
                  className="flex flex-col items-center p-4 bg-green-50 hover:bg-green-100 rounded-xl transition-colors group"
                >
                  <TrendingUp className="w-8 h-8 text-green-600 mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium text-green-900">Adicionar Receita</span>
                </button>
                
                <button 
                  onClick={openExpenseModal}
                  className="flex flex-col items-center p-4 bg-red-50 hover:bg-red-100 rounded-xl transition-colors group"
                >
                  <TrendingDown className="w-8 h-8 text-red-600 mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium text-red-900">Adicionar Despesa</span>
                </button>
                
                <button 
                  onClick={openTransferModal}
                  className="flex flex-col items-center p-4 bg-purple-50 hover:bg-purple-100 rounded-xl transition-colors group"
                >
                  <Plus className="w-8 h-8 text-purple-600 mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium text-purple-900">Transferir</span>
                </button>
                
                <button 
                  onClick={openReportsModal}
                  className="flex flex-col items-center p-4 bg-orange-50 hover:bg-orange-100 rounded-xl transition-colors group"
                >
                  <FileText className="w-8 h-8 text-orange-600 mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium text-orange-900">Relatórios</span>
                </button>
              </div>
            </div>
          </>
        )}

        {activeView === 'transactions' && (
          <TransactionsView 
            transactions={transactions}
            accounts={accounts}
            categories={categories}
            onRefresh={loadDashboard}
            onEdit={(transaction) => {
              setEditingItem(transaction);
              setTransactionType(transaction.type);
              setShowTransactionModal(true);
            }}
          />
        )}

        {activeView === 'accounts' && (
          <AccountsView 
            accounts={accounts}
            onRefresh={loadDashboard}
            onEdit={(account) => {
              setEditingItem(account);
              setShowAccountModal(true);
            }}
            onCreateNew={openNewAccountModal}
          />
        )}

        {activeView === 'budgets' && (
          <BudgetsView 
            budgets={budgets}
            categories={categories}
            summary={summary}
            onRefresh={loadDashboard}
            onCreateNew={openBudgetModal}
          />
        )}
      </div>

      {/* Modals */}
      {showAccountModal && (
        <AccountModal
          account={editingItem}
          onClose={() => {
            setShowAccountModal(false);
            setEditingItem(null);
          }}
          onCreate={handleCreateAccount}
        />
      )}

      {showTransactionModal && (
        <TransactionModal
          transaction={editingItem}
          type={transactionType}
          accounts={accounts}
          categories={categories}
          onClose={() => {
            setShowTransactionModal(false);
            setEditingItem(null);
          }}
          onCreate={handleCreateTransaction}
        />
      )}

      {showTransferModal && (
        <TransferModal
          accounts={accounts}
          onClose={() => setShowTransferModal(false)}
          onCreate={handleCreateTransfer}
        />
      )}

      {showBudgetModal && (
        <BudgetModal
          categories={categories}
          onClose={() => setShowBudgetModal(false)}
          onCreate={handleCreateBudget}
        />
      )}

      {showReportsModal && (
        <ReportsModal
          summary={summary}
          transactions={transactions}
          accounts={accounts}
          onClose={() => setShowReportsModal(false)}
        />
      )}

      <Toaster position="top-right" />
    </div>
  );
};

// Additional Views Components (simplified for brevity)
const TransactionsView = ({ transactions, accounts, categories, onRefresh, onEdit }) => {
  return (
    <div className="bg-white rounded-xl shadow-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Todas as Transações</h2>
      </div>
      <div className="p-6">
        {/* Transaction filters and list would go here */}
        <p className="text-gray-500">Lista completa de transações em desenvolvimento...</p>
      </div>
    </div>
  );
};

const AccountsView = ({ accounts, onRefresh, onEdit, onCreateNew }) => {
  return (
    <div className="bg-white rounded-xl shadow-lg">
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Gerenciar Contas</h2>
        <button
          onClick={onCreateNew}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus size={16} />
          Nova Conta
        </button>
      </div>
      <div className="p-6">
        {/* Account management interface would go here */}
        <p className="text-gray-500">Gerenciamento de contas em desenvolvimento...</p>
      </div>
    </div>
  );
};

const BudgetsView = ({ budgets, categories, summary, onRefresh, onCreateNew }) => {
  return (
    <div className="bg-white rounded-xl shadow-lg">
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Orçamentos</h2>
        <button
          onClick={onCreateNew}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
        >
          <Plus size={16} />
          Novo Orçamento
        </button>
      </div>
      <div className="p-6">
        {/* Budget management interface would go here */}
        <p className="text-gray-500">Sistema de orçamentos em desenvolvimento...</p>
      </div>
    </div>
  );
};

// Enhanced Modals will continue...
// Due to length constraints, I'll include key modals:

// Account Modal Component
const AccountModal = ({ account, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: account?.name || '',
    type: account?.type || 'Conta Corrente',
    institution: account?.institution || '',
    initial_balance: account?.initial_balance || 0,
    credit_limit: account?.credit_limit || 0,
    invoice_due_date: account?.invoice_due_date || '',
    color_hex: account?.color_hex || '#4F46E5'
  });

  const accountTypes = [
    'Conta Corrente', 'Poupança', 'Cartão de Crédito', 
    'Investimento', 'Dinheiro em Espécie', 'Outros'
  ];

  const institutions = [
    'Itaú', 'Bradesco', 'Banco do Brasil', 'Caixa Econômica Federal',
    'Santander', 'NuBank', 'C6 Bank', 'Inter', 'PicPay', 'Sicoob',
    'Sicredi', 'Banco Safra', 'XP Investimentos', 'BTG Pactual', 
    'Genial Investimentos', 'Outro'
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h3 className="text-xl font-semibold mb-6">
          {account ? 'Editar Conta' : 'Nova Conta'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nome da Conta *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="Ex: Conta Corrente Principal"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Conta *</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
            >
              {accountTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Instituição Financeira</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.institution}
              onChange={(e) => setFormData({...formData, institution: e.target.value})}
            >
              <option value="">Selecione uma instituição</option>
              {institutions.map(institution => (
                <option key={institution} value={institution}>{institution}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Saldo Inicial *</label>
            <input
              type="number"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.initial_balance}
              onChange={(e) => setFormData({...formData, initial_balance: parseFloat(e.target.value) || 0})}
              placeholder="0,00"
            />
          </div>

          {formData.type === 'Cartão de Crédito' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Limite de Crédito</label>
                <input
                  type="number"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  value={formData.credit_limit}
                  onChange={(e) => setFormData({...formData, credit_limit: parseFloat(e.target.value) || 0})}
                  placeholder="0,00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Data de Vencimento da Fatura</label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  value={formData.invoice_due_date}
                  onChange={(e) => setFormData({...formData, invoice_due_date: e.target.value})}
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Cor da Conta</label>
            <input
              type="color"
              className="w-full h-12 border border-gray-300 rounded-lg cursor-pointer"
              value={formData.color_hex}
              onChange={(e) => setFormData({...formData, color_hex: e.target.value})}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {account ? 'Atualizar' : 'Criar'} Conta
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Transaction Modal Component
const TransactionModal = ({ transaction, type, accounts, categories, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    description: transaction?.description || '',
    value: transaction?.value || 0,
    type: type,
    transaction_date: transaction?.transaction_date ? 
      formatDateForInput(transaction.transaction_date) : 
      formatDateForInput(new Date()),
    account_id: transaction?.account_id || '',
    category_id: transaction?.category_id || '',
    observation: transaction?.observation || '',
    is_recurring: transaction?.is_recurring || false,
    recurrence_interval: transaction?.recurrence_interval || '',
    status: transaction?.status || 'Pago'
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
  const recurrenceOptions = ['Diária', 'Semanal', 'Quinzenal', 'Mensal', 'Anual'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h3 className="text-xl font-semibold mb-6">
          {transaction ? `Editar ${type}` : `Adicionar ${type}`}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Descrição *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder={type === 'Receita' ? 'Ex: Salário' : 'Ex: Supermercado'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Valor (R$) *</label>
            <input
              type="number"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.value}
              onChange={(e) => setFormData({...formData, value: e.target.value})}
              placeholder="0,00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Data *</label>
            <input
              type="date"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.transaction_date}
              onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Conta *</label>
            <select
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.account_id}
              onChange={(e) => setFormData({...formData, account_id: e.target.value})}
            >
              <option value="">Selecione uma conta</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.name} ({formatCurrency(account.current_balance)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Categoria</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.category_id}
              onChange={(e) => setFormData({...formData, category_id: e.target.value})}
            >
              <option value="">Selecione uma categoria</option>
              {relevantCategories.map(category => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.status}
              onChange={(e) => setFormData({...formData, status: e.target.value})}
            >
              <option value="Pago">Pago</option>
              <option value="Pendente">Pendente</option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_recurring"
              className="mr-2"
              checked={formData.is_recurring}
              onChange={(e) => setFormData({...formData, is_recurring: e.target.checked})}
            />
            <label htmlFor="is_recurring" className="text-sm font-medium text-gray-700">
              Transação Recorrente
            </label>
          </div>

          {formData.is_recurring && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Frequência</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.recurrence_interval}
                onChange={(e) => setFormData({...formData, recurrence_interval: e.target.value})}
              >
                <option value="">Selecione a frequência</option>
                {recurrenceOptions.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Observação</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              rows="3"
              value={formData.observation}
              onChange={(e) => setFormData({...formData, observation: e.target.value})}
              placeholder="Observações adicionais..."
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={`px-4 py-2 text-white rounded-lg transition-colors ${
                type === 'Receita' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {transaction ? 'Atualizar' : 'Adicionar'} {type}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Transfer Modal Component
const TransferModal = ({ accounts, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    from_account_id: '',
    to_account_id: '',
    value: 0,
    description: '',
    transaction_date: formatDateForInput(new Date())
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.from_account_id === formData.to_account_id) {
      toast.error('Contas de origem e destino devem ser diferentes');
      return;
    }
    
    const transferData = {
      ...formData,
      transaction_date: new Date(formData.transaction_date).toISOString(),
      value: parseFloat(formData.value)
    };
    onCreate(transferData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 className="text-xl font-semibold mb-6">Transferência entre Contas</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Conta de Origem *</label>
            <select
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.from_account_id}
              onChange={(e) => setFormData({...formData, from_account_id: e.target.value})}
            >
              <option value="">Selecione a conta de origem</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.name} ({formatCurrency(account.current_balance)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Conta de Destino *</label>
            <select
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.to_account_id}
              onChange={(e) => setFormData({...formData, to_account_id: e.target.value})}
            >
              <option value="">Selecione a conta de destino</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.name} ({formatCurrency(account.current_balance)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Valor (R$) *</label>
            <input
              type="number"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.value}
              onChange={(e) => setFormData({...formData, value: e.target.value})}
              placeholder="0,00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Descrição *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Motivo da transferência"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Data *</label>
            <input
              type="date"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.transaction_date}
              onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Realizar Transferência
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Budget Modal Component
const BudgetModal = ({ categories, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    category_id: '',
    budget_amount: 0,
    month_year: new Date().toISOString().slice(0, 7) // YYYY-MM format
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const budgetData = {
      ...formData,
      budget_amount: parseFloat(formData.budget_amount)
    };
    onCreate(budgetData);
  };

  const expenseCategories = categories.filter(cat => cat.type === 'Despesa');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 className="text-xl font-semibold mb-6">Definir Orçamento</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Categoria *</label>
            <select
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.category_id}
              onChange={(e) => setFormData({...formData, category_id: e.target.value})}
            >
              <option value="">Selecione uma categoria de despesa</option>
              {expenseCategories.map(category => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Valor do Orçamento (R$) *</label>
            <input
              type="number"
              step="0.01"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.budget_amount}
              onChange={(e) => setFormData({...formData, budget_amount: e.target.value})}
              placeholder="0,00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mês/Ano *</label>
            <input
              type="month"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.month_year}
              onChange={(e) => setFormData({...formData, month_year: e.target.value})}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Definir Orçamento
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Reports Modal Component
const ReportsModal = ({ summary, transactions, accounts, onClose }) => {
  const [reportType, setReportType] = useState('overview');
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });

  const exportToCSV = () => {
    // Simple CSV export functionality
    const csvData = transactions.map(t => ({
      Data: formatDate(t.transaction_date),
      Descrição: t.description,
      Valor: t.value,
      Tipo: t.type,
      Conta: accounts.find(a => a.id === t.account_id)?.name || 'N/A'
    }));

    const csvContent = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `relatorio-financeiro-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    toast.success('Relatório exportado com sucesso!');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-semibold text-gray-900">Relatórios Financeiros</h3>
          <div className="flex items-center gap-3">
            <button
              onClick={exportToCSV}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              <Download size={16} />
              Exportar CSV
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl p-1"
            >
              ×
            </button>
          </div>
        </div>

        {/* Report Controls */}
        <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Relatório</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="overview">Visão Geral</option>
              <option value="cashflow">Fluxo de Caixa</option>
              <option value="categories">Por Categorias</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Inicial</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Final</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Report Content */}
        <div className="space-y-8">
          {/* Summary Section */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-blue-50 p-6 rounded-lg">
              <h4 className="font-medium text-blue-800 mb-2">Saldo Total</h4>
              <p className="text-3xl font-bold text-blue-900">
                {formatCurrency(summary?.total_balance || 0)}
              </p>
            </div>
            
            <div className="bg-green-50 p-6 rounded-lg">
              <h4 className="font-medium text-green-800 mb-2">Receitas Totais</h4>
              <p className="text-3xl font-bold text-green-900">
                {formatCurrency(summary?.monthly_income || 0)}
              </p>
            </div>
            
            <div className="bg-red-50 p-6 rounded-lg">
              <h4 className="font-medium text-red-800 mb-2">Despesas Totais</h4>
              <p className="text-3xl font-bold text-red-900">
                {formatCurrency(summary?.monthly_expenses || 0)}
              </p>
            </div>

            <div className="bg-purple-50 p-6 rounded-lg">
              <h4 className="font-medium text-purple-800 mb-2">Saldo Líquido</h4>
              <p className={`text-3xl font-bold ${
                (summary?.monthly_net || 0) >= 0 ? 'text-green-900' : 'text-red-900'
              }`}>
                {formatCurrency(summary?.monthly_net || 0)}
              </p>
            </div>
          </div>

          {/* Accounts Section */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Resumo por Conta</h4>
            <div className="bg-white border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Conta</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Instituição</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Saldo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {accounts.map(account => (
                    <tr key={account.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <div 
                            className="w-4 h-4 rounded-full mr-3"
                            style={{ backgroundColor: account.color_hex }}
                          ></div>
                          <span className="font-medium">{account.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-600">{account.type}</td>
                      <td className="px-6 py-4 text-gray-600">{account.institution || 'N/A'}</td>
                      <td className="px-6 py-4 text-right font-bold">
                        {formatCurrency(account.current_balance)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Transactions */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Transações Recentes</h4>
            <div className="bg-white border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descrição</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Valor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {transactions.slice(0, 10).map(transaction => (
                    <tr key={transaction.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {formatDate(transaction.transaction_date)}
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-medium">{transaction.description}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          transaction.type === 'Receita' ? 
                            'bg-green-100 text-green-800' : 
                            'bg-red-100 text-red-800'
                        }`}>
                          {transaction.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={`font-bold ${
                          transaction.type === 'Receita' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {transaction.type === 'Receita' ? '+' : '-'}
                          {formatCurrency(transaction.value)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="flex justify-end mt-8">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-white text-xl font-medium">Carregando OrçaZenFinanceiro...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {user ? <Dashboard /> : <LoginForm />}
      <Toaster position="top-right" />
    </div>
  );
}

function AppWrapper() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWrapper;