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
      console.log('Registration attempt for:', email);
      const response = await axios.post(`${API}/auth/register`, { 
        name, email, password, confirm_password: confirmPassword 
      });
      
      // New registration flow - no immediate login
      console.log('Registration response:', response.data);
      toast.success(response.data.message || 'Conta criada! Verifique seu email para ativar.');
      
      return { success: true, requiresVerification: true };
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
  const [showForgotPassword, setShowForgotPassword] = useState(false);
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
      if (showForgotPassword) {
        // Handle forgot password
        const response = await axios.post(`${API}/auth/forgot-password`, {
          email: formData.email
        });
        toast.success('Instruções enviadas para seu email!');
        setShowForgotPassword(false);
        setFormData({ name: '', email: '', password: '', confirmPassword: '' });
      } else if (!isLogin && formData.password !== formData.confirmPassword) {
        setError('Senhas não coincidem');
        setLoading(false);
        return;
      } else {
        const result = isLogin 
          ? await login(formData.email, formData.password)
          : await register(formData.name, formData.email, formData.password, formData.confirmPassword);

        if (!result.success) {
          setError(result.message);
          toast.error(result.message);
        }
      }
      // Don't set loading to false here - let the context handle the redirect
    } catch (error) {
      console.error('Form submit error:', error);
      const errorMessage = error.response?.data?.detail || 'Erro interno. Tente novamente.';
      setError(errorMessage);
      toast.error(errorMessage);
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

        {!showForgotPassword ? (
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
            <button
              type="button"
              className={`flex-1 py-2 text-center font-medium transition-all ${
                isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              } rounded-md`}
              onClick={() => {
                setIsLogin(true);
                setShowForgotPassword(false);
                setError('');
                setFormData({ name: '', email: '', password: '', confirmPassword: '' });
              }}
            >
              Entrar
            </button>
            <button
              type="button"
              className={`flex-1 py-2 text-center font-medium transition-all ${
                !isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              } rounded-md`}
              onClick={() => {
                setIsLogin(false);
                setShowForgotPassword(false);
                setError('');
                setFormData({ name: '', email: '', password: '', confirmPassword: '' });
              }}
            >
              Cadastrar
            </button>
          </div>
        ) : (
          <div className="text-center mb-6">
            <h3 className="text-lg font-semibold text-gray-800">Recuperar Senha</h3>
            <p className="text-sm text-gray-600 mt-1">Digite seu email para receber instruções</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && !showForgotPassword && (
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
          
          {!showForgotPassword && (
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
          )}

          {!isLogin && !showForgotPassword && (
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
            {loading ? 'Carregando...' : 
              showForgotPassword ? 'Enviar Instruções' :
              isLogin ? 'Entrar' : 'Criar Conta'
            }
          </button>
        </form>

        <div className="text-center mt-4 space-y-2">
          {isLogin && !showForgotPassword && (
            <button 
              type="button"
              className="text-blue-600 hover:text-blue-800 text-sm transition-colors"
              onClick={() => {
                setShowForgotPassword(true);
                setError('');
                setFormData({ name: '', email: '', password: '', confirmPassword: '' });
              }}
            >
              Esqueci minha senha
            </button>
          )}
          
          {showForgotPassword && (
            <button 
              type="button"
              className="text-gray-600 hover:text-gray-800 text-sm transition-colors"
              onClick={() => {
                setShowForgotPassword(false);
                setIsLogin(true);
                setError('');
                setFormData({ name: '', email: '', password: '', confirmPassword: '' });
              }}
            >
              ← Voltar ao login
            </button>
          )}
        </div>
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
  const [goals, setGoals] = useState([]);
  const [goalsStats, setGoalsStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [showNotificationPanel, setShowNotificationPanel] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('dashboard');
  
  // Modal states
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [showTransactionModal, setShowTransactionModal] = useState(false);
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [showReportsModal, setShowReportsModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showContributeModal, setShowContributeModal] = useState(false);
  const [transactionType, setTransactionType] = useState('');
  const [editingItem, setEditingItem] = useState(null);

  const { user, logout } = useAuth();

  const loadDashboard = async () => {
    try {
      console.log('Loading dashboard data...');
      
      // Load data sequentially to avoid overloading
      const summaryRes = await axios.get(`${API}/dashboard/summary`);
      setSummary(summaryRes.data);
      
      const accountsRes = await axios.get(`${API}/accounts`);
      setAccounts(accountsRes.data);
      
      const transactionsRes = await axios.get(`${API}/transactions?limit=10`);
      setTransactions(transactionsRes.data);
      
      const categoriesRes = await axios.get(`${API}/categories`);
      setCategories(categoriesRes.data);
      
      try {
        const budgetsRes = await axios.get(`${API}/budgets`);
        setBudgets(budgetsRes.data);
      } catch (budgetError) {
        console.log('Budget loading failed, continuing without budgets');
        setBudgets([]);
      }

      try {
        const goalsRes = await axios.get(`${API}/goals`);
        setGoals(goalsRes.data);
        
        const goalsStatsRes = await axios.get(`${API}/goals/statistics`);
        setGoalsStats(goalsStatsRes.data);
      } catch (goalsError) {
        console.log('Goals loading failed, continuing without goals');
        setGoals([]);
        setGoalsStats(null);
      }
      
  const generateNotifications = () => {
    const newNotifications = [];
    const now = new Date();

    // Check for overdue transactions
    transactions.forEach(transaction => {
      if (transaction.status === 'Pendente' && new Date(transaction.transaction_date) < now) {
        newNotifications.push({
          id: `overdue-${transaction.id}`,
          type: 'warning',
          title: 'Transação em atraso',
          message: `${transaction.description} - ${formatCurrency(transaction.value)}`,
          time: new Date().toISOString(),
          read: false
        });
      }
    });

    // Check for budget alerts
    budgets.forEach(budget => {
      const spent = summary?.categories?.find(c => c.id === budget.category_id)?.spent || 0;
      const percentage = (spent / budget.budget_amount) * 100;
      
      if (percentage >= 100) {
        newNotifications.push({
          id: `budget-exceeded-${budget.id}`,
          type: 'error',
          title: 'Orçamento ultrapassado',
          message: `Categoria excedeu o limite mensal`,
          time: new Date().toISOString(),
          read: false
        });
      } else if (percentage >= 80) {
        newNotifications.push({
          id: `budget-warning-${budget.id}`,
          type: 'warning',
          title: 'Orçamento próximo do limite',
          message: `${percentage.toFixed(0)}% do orçamento utilizado`,
          time: new Date().toISOString(),
          read: false
        });
      }
    });

    // Check for goal milestones
    goals.forEach(goal => {
      const progress = (goal.current_amount / goal.target_amount) * 100;
      if (progress >= 75 && progress < 100) {
        const remainingDays = Math.ceil((new Date(goal.target_date) - now) / (1000 * 60 * 60 * 24));
        newNotifications.push({
          id: `goal-milestone-${goal.id}`,
          type: 'success',
          title: 'Meta quase atingida!',
          message: `${goal.name} - ${progress.toFixed(0)}% completa (${remainingDays} dias restantes)`,
          time: new Date().toISOString(),
          read: false
        });
      }
    });

    // Low balance alerts
    accounts.forEach(account => {
      if (account.current_balance < 100 && account.type !== 'Cartão de Crédito') {
        newNotifications.push({
          id: `low-balance-${account.id}`,
          type: 'warning',
          title: 'Saldo baixo',
          message: `${account.name} - ${formatCurrency(account.current_balance)}`,
          time: new Date().toISOString(),
          read: false
        });
      }
    });

    setNotifications(newNotifications);
    setUnreadNotifications(newNotifications.filter(n => !n.read).length);
  };

      console.log('Dashboard loaded successfully');
      
      // Generate notifications after loading data
      setTimeout(generateNotifications, 1000);
      
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      
      // Only logout if it's a clear auth error
      if (error.response?.status === 401) {
        toast.error('Sessão expirada. Faça login novamente.');
        logout();
      } else {
        toast.error('Erro ao carregar dados. Verifique sua conexão.');
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // Close notification panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showNotificationPanel && !event.target.closest('.notification-panel')) {
        setShowNotificationPanel(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNotificationPanel]);

  // Close notification panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showNotificationPanel && !event.target.closest('.notification-panel')) {
        setShowNotificationPanel(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNotificationPanel]);

  // Event handlers
  const handleCreateAccount = async (accountData) => {
    try {
      if (editingItem && editingItem.id) {
        // Update existing account
        await axios.put(`${API}/accounts/${editingItem.id}`, accountData);
        toast.success('Conta atualizada com sucesso!');
      } else {
        // Create new account
        await axios.post(`${API}/accounts`, accountData);
        toast.success('Conta criada com sucesso!');
      }
      await loadDashboard();
      setShowAccountModal(false);
      setEditingItem(null);
    } catch (error) {
      toast.error('Erro ao salvar conta: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleDeleteAccount = async (accountId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta conta? Esta ação não pode ser desfeita.')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/accounts/${accountId}`);
      await loadDashboard();
      toast.success('Conta excluída com sucesso!');
    } catch (error) {
      toast.error('Erro ao excluir conta: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleCreateTransaction = async (transactionData) => {
    try {
      if (editingItem && editingItem.id) {
        // Update existing transaction
        await axios.put(`${API}/transactions/${editingItem.id}`, transactionData);
        toast.success('Transação atualizada com sucesso!');
      } else {
        // Create new transaction
        await axios.post(`${API}/transactions`, transactionData);
        toast.success('Transação adicionada com sucesso!');
      }
      await loadDashboard();
      setShowTransactionModal(false);
      setEditingItem(null);
    } catch (error) {
      toast.error('Erro ao salvar transação: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleDeleteTransaction = async (transactionId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta transação? Esta ação não pode ser desfeita.')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/transactions/${transactionId}`);
      await loadDashboard();
      toast.success('Transação excluída com sucesso!');
    } catch (error) {
      toast.error('Erro ao excluir transação: ' + (error.response?.data?.detail || 'Erro desconhecido'));
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
      if (editingItem && editingItem.id) {
        // Update existing budget
        await axios.put(`${API}/budgets/${editingItem.id}`, budgetData);
        toast.success('Orçamento atualizado com sucesso!');
      } else {
        // Create new budget
        await axios.post(`${API}/budgets`, budgetData);
        toast.success('Orçamento definido com sucesso!');
      }
      await loadDashboard();
      setShowBudgetModal(false);
      setEditingItem(null);
    } catch (error) {
      toast.error('Erro ao salvar orçamento: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleDeleteBudget = async (budgetId) => {
    if (!window.confirm('Tem certeza que deseja excluir este orçamento?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/budgets/${budgetId}`);
      await loadDashboard();
      toast.success('Orçamento excluído com sucesso!');
    } catch (error) {
      toast.error('Erro ao excluir orçamento: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleCreateGoal = async (goalData) => {
    try {
      if (editingItem && editingItem.id) {
        // Update existing goal
        await axios.put(`${API}/goals/${editingItem.id}`, goalData);
        toast.success('Meta atualizada com sucesso!');
      } else {
        // Create new goal
        await axios.post(`${API}/goals`, goalData);
        toast.success('Meta criada com sucesso!');
      }
      await loadDashboard();
      setShowGoalModal(false);
      setEditingItem(null);
    } catch (error) {
      toast.error('Erro ao salvar meta: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleDeleteGoal = async (goalId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta meta?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/goals/${goalId}`);
      await loadDashboard();
      toast.success('Meta excluída com sucesso!');
    } catch (error) {
      toast.error('Erro ao excluir meta: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleContributeToGoal = async (goalId, amount) => {
    try {
      const response = await axios.post(`${API}/goals/${goalId}/contribute?amount=${amount}`);
      await loadDashboard();
      setShowContributeModal(false);
      setEditingItem(null);
      
      if (response.data.goal_achieved) {
        toast.success('🎉 Parabéns! Você atingiu sua meta!');
      } else {
        toast.success('Contribuição adicionada com sucesso!');
      }
    } catch (error) {
      toast.error('Erro ao fazer contribuição: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleMarkTransactionPaid = async (transactionId) => {
    try {
      // Get the transaction data first
      const transaction = transactions.find(t => t.id === transactionId);
      if (!transaction) {
        toast.error('Transação não encontrada');
        return;
      }

      // Update transaction with new data including status
      const updatedTransactionData = {
        description: transaction.description,
        value: transaction.value,
        type: transaction.type,
        transaction_date: transaction.transaction_date,
        account_id: transaction.account_id,
        category_id: transaction.category_id,
        observation: transaction.observation,
        is_recurring: transaction.is_recurring,
        recurrence_interval: transaction.recurrence_interval,
        status: 'Pago'
      };

      await axios.put(`${API}/transactions/${transactionId}`, updatedTransactionData);
      await loadDashboard();
      toast.success('Transação marcada como paga!');
    } catch (error) {
      toast.error('Erro ao atualizar transação');
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

  // Chart data generators
  const generateBalanceEvolutionData = () => {
    const months = [];
    const currentDate = new Date();
    let runningBalance = summary?.total_balance || 0;
    
    for (let i = 11; i >= 0; i--) {
      const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
      const monthName = date.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' });
      
      // Simulate balance evolution (in real scenario, this would come from historical data)
      const variance = (Math.random() - 0.5) * 1000;
      runningBalance += variance;
      
      months.push({
        month: monthName,
        balance: Math.max(0, runningBalance) // Ensure non-negative balance
      });
    }
    
    return months;
  };

  const generateIncomeVsExpensesData = () => {
    const months = [];
    const currentDate = new Date();
    
    for (let i = 11; i >= 0; i--) {
      const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
      const monthName = date.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' });
      
      // Use current month data for the latest month, simulate for others
      if (i === 0) {
        months.push({
          month: monthName,
          income: summary?.monthly_income || 0,
          expenses: summary?.monthly_expenses || 0
        });
      } else {
        months.push({
          month: monthName,
          income: Math.random() * 5000 + 1000,
          expenses: Math.random() * 4000 + 800
        });
      }
    }
    
    return months;
  };
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
                  onClick={() => setActiveView('goals')}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    activeView === 'goals' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Metas
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
              <div className="flex items-center space-x-3">
                <span className="text-gray-600 text-sm">Bem-vindo,</span>
                <span className="font-medium text-gray-900">{user?.name}</span>
              </div>
              
              <div className="relative">
                <button 
                  onClick={() => setShowNotificationPanel(!showNotificationPanel)}
                  className="p-2 text-gray-400 hover:text-gray-600 relative transition-colors"
                >
                  <Bell size={20} />
                  {unreadNotifications > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center animate-pulse">
                      {unreadNotifications}
                    </span>
                  )}
                </button>
                
                {showNotificationPanel && (
                  <div className="notification-panel absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border z-50 max-h-96 overflow-y-auto">
                    <div className="p-4 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-gray-900">Notificações</h3>
                        <button
                          onClick={() => {
                            setNotifications(notifications.map(n => ({ ...n, read: true })));
                            setUnreadNotifications(0);
                          }}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          Marcar todas como lidas
                        </button>
                      </div>
                    </div>
                    
                    <div className="max-h-64 overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="p-4 text-center text-gray-500">
                          <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                          <p>Nenhuma notificação</p>
                        </div>
                      ) : (
                        notifications.map((notification) => (
                          <div
                            key={notification.id}
                            className={`p-4 border-b border-gray-100 hover:bg-gray-50 ${
                              !notification.read ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                            }`}
                          >
                            <div className="flex items-start">
                              <div className={`w-2 h-2 rounded-full mt-2 mr-3 ${
                                notification.type === 'error' ? 'bg-red-500' :
                                notification.type === 'warning' ? 'bg-yellow-500' :
                                notification.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
                              }`} />
                              <div className="flex-1">
                                <p className="font-medium text-gray-900 text-sm">
                                  {notification.title}
                                </p>
                                <p className="text-gray-600 text-sm">
                                  {notification.message}
                                </p>
                                <p className="text-xs text-gray-400 mt-1">
                                  {new Date(notification.time).toLocaleString('pt-BR')}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
              
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

            {/* Advanced Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Balance Evolution Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Evolução do Saldo (12 meses)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={generateBalanceEvolutionData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} />
                    <Tooltip formatter={(value) => [formatCurrency(value), 'Saldo']} />
                    <Line 
                      type="monotone" 
                      dataKey="balance" 
                      stroke="#3B82F6" 
                      strokeWidth={3}
                      dot={{ r: 6 }}
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Income vs Expenses Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Receitas vs Despesas (12 meses)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={generateIncomeVsExpensesData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} />
                    <Tooltip formatter={(value, name) => [formatCurrency(value), name]} />
                    <Bar dataKey="income" fill="#10B981" name="Receitas" />
                    <Bar dataKey="expenses" fill="#EF4444" name="Despesas" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Próximas Contas Section */}
            {summary?.pending_transactions && summary.pending_transactions.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg mb-8">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Bell className="w-5 h-5 text-orange-500" />
                    Próximas Contas a Pagar/Receber (15 dias)
                  </h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {summary.pending_transactions.map((transaction) => (
                      <div key={transaction.id} className="flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50 transition-colors">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-3 ${
                            transaction.type === 'Receita' ? 'bg-green-500' : 'bg-red-500'
                          }`}></div>
                          <div>
                            <p className="font-medium text-gray-900">{transaction.description}</p>
                            <p className="text-sm text-gray-500">
                              {formatDate(transaction.transaction_date)} • {transaction.type}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <p className={`font-bold ${
                            transaction.type === 'Receita' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {formatCurrency(transaction.value)}
                          </p>
                          <button
                            onClick={() => handleMarkTransactionPaid(transaction.id)}
                            className="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            Marcar como {transaction.type === 'Receita' ? 'Recebida' : 'Paga'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

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
                        <div key={account.id} className="flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50 transition-colors group">
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
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <p className="font-bold text-gray-900">{formatCurrency(account.current_balance)}</p>
                              <p className="text-xs text-gray-500">Saldo atual</p>
                            </div>
                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => {
                                  setEditingItem(account);
                                  setShowAccountModal(true);
                                }}
                                className="p-1 text-blue-600 hover:text-blue-800"
                                title="Editar conta"
                              >
                                <Edit size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteAccount(account.id)}
                                className="p-1 text-red-600 hover:text-red-800"
                                title="Excluir conta"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
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
                        <div key={transaction.id} className="flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50 transition-colors group">
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
                          <div className="flex items-center gap-3">
                            <p className={`font-bold ${
                              transaction.type === 'Receita' ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {transaction.type === 'Receita' ? '+' : '-'}{formatCurrency(transaction.value)}
                            </p>
                            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => {
                                  setEditingItem(transaction);
                                  setTransactionType(transaction.type);
                                  setShowTransactionModal(true);
                                }}
                                className="p-1 text-blue-600 hover:text-blue-800"
                                title="Editar transação"
                              >
                                <Edit size={16} />
                              </button>
                              <button
                                onClick={() => handleDeleteTransaction(transaction.id)}
                                className="p-1 text-red-600 hover:text-red-800"
                                title="Excluir transação"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </div>
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
            onDelete={handleDeleteTransaction}
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
            onDelete={handleDeleteAccount}
            onCreateNew={openNewAccountModal}
          />
        )}

        {activeView === 'goals' && (
          <GoalsView 
            goals={goals}
            goalsStats={goalsStats}
            onRefresh={loadDashboard}
            onCreateNew={() => {
              setEditingItem(null);
              setShowGoalModal(true);
            }}
            onEdit={(goal) => {
              setEditingItem(goal);
              setShowGoalModal(true);
            }}
            onDelete={handleDeleteGoal}
            onContribute={(goal) => {
              setEditingItem(goal);
              setShowContributeModal(true);
            }}
          />
        )}

        {activeView === 'budgets' && (
          <BudgetsView 
            budgets={budgets}
            categories={categories}
            summary={summary}
            onRefresh={loadDashboard}
            onCreateNew={openBudgetModal}
            onEdit={(budget) => {
              setEditingItem(budget);
              setShowBudgetModal(true);
            }}
            onDelete={handleDeleteBudget}
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
          budget={editingItem}
          categories={categories}
          onClose={() => {
            setShowBudgetModal(false);
            setEditingItem(null);
          }}
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

      {showGoalModal && (
        <GoalModal
          goal={editingItem}
          onClose={() => {
            setShowGoalModal(false);
            setEditingItem(null);
          }}
          onCreate={handleCreateGoal}
        />
      )}

      {showContributeModal && (
        <ContributeModal
          goal={editingItem}
          onClose={() => {
            setShowContributeModal(false);
            setEditingItem(null);
          }}
          onContribute={handleContributeToGoal}
        />
      )}

      <Toaster position="top-right" />
    </div>
  );
};

// Enhanced Views Components
const TransactionsView = ({ transactions, accounts, categories, onRefresh, onEdit, onDelete }) => {
  const [filteredTransactions, setFilteredTransactions] = useState(transactions);
  const [filters, setFilters] = useState({
    search: '',
    type: '',
    account: '',
    category: '',
    dateStart: '',
    dateEnd: '',
    status: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // Filter transactions
  useEffect(() => {
    let filtered = [...transactions];
    
    if (filters.search) {
      filtered = filtered.filter(t => 
        t.description.toLowerCase().includes(filters.search.toLowerCase()) ||
        t.value.toString().includes(filters.search)
      );
    }
    
    if (filters.type) {
      filtered = filtered.filter(t => t.type === filters.type);
    }
    
    if (filters.account) {
      filtered = filtered.filter(t => t.account_id === filters.account);
    }
    
    if (filters.category) {
      filtered = filtered.filter(t => t.category_id === filters.category);
    }
    
    if (filters.status) {
      filtered = filtered.filter(t => t.status === filters.status);
    }
    
    if (filters.dateStart) {
      filtered = filtered.filter(t => new Date(t.transaction_date) >= new Date(filters.dateStart));
    }
    
    if (filters.dateEnd) {
      filtered = filtered.filter(t => new Date(t.transaction_date) <= new Date(filters.dateEnd));
    }
    
    setFilteredTransactions(filtered);
    setCurrentPage(1);
  }, [transactions, filters]);

  // Pagination
  const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
  const paginatedTransactions = filteredTransactions.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const resetFilters = () => {
    setFilters({
      search: '',
      type: '',
      account: '',
      category: '',
      dateStart: '',
      dateEnd: '',
      status: ''
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Gerenciar Transações</h2>
          <div className="text-sm text-gray-500">
            {filteredTransactions.length} de {transactions.length} transações
          </div>
        </div>

        {/* Advanced Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-7 gap-4">
          <input
            type="text"
            placeholder="Buscar descrição ou valor..."
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.search}
            onChange={(e) => setFilters({...filters, search: e.target.value})}
          />

          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.type}
            onChange={(e) => setFilters({...filters, type: e.target.value})}
          >
            <option value="">Todos os tipos</option>
            <option value="Receita">Receitas</option>
            <option value="Despesa">Despesas</option>
          </select>

          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.account}
            onChange={(e) => setFilters({...filters, account: e.target.value})}
          >
            <option value="">Todas as contas</option>
            {accounts.map(account => (
              <option key={account.id} value={account.id}>{account.name}</option>
            ))}
          </select>

          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.status}
            onChange={(e) => setFilters({...filters, status: e.target.value})}
          >
            <option value="">Todos os status</option>
            <option value="Pago">Pago</option>
            <option value="Pendente">Pendente</option>
          </select>

          <input
            type="date"
            placeholder="Data inicial"
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.dateStart}
            onChange={(e) => setFilters({...filters, dateStart: e.target.value})}
          />

          <input
            type="date"
            placeholder="Data final"
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.dateEnd}
            onChange={(e) => setFilters({...filters, dateEnd: e.target.value})}
          />

          <button
            onClick={resetFilters}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
          >
            <Filter size={16} />
            Limpar
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrição</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoria</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Conta</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Valor</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedTransactions.map((transaction) => {
              const account = accounts.find(a => a.id === transaction.account_id);
              const category = categories.find(c => c.id === transaction.category_id);
              
              return (
                <tr key={transaction.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(transaction.transaction_date)}
                  </td>
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{transaction.description}</div>
                      {transaction.observation && (
                        <div className="text-sm text-gray-500">{transaction.observation}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {category?.name || 'Sem categoria'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center">
                      {account && (
                        <div 
                          className="w-3 h-3 rounded-full mr-2"
                          style={{ backgroundColor: account.color_hex }}
                        ></div>
                      )}
                      {account?.name || 'Conta removida'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      transaction.type === 'Receita' ? 
                        'bg-green-100 text-green-800' : 
                        'bg-red-100 text-red-800'
                    }`}>
                      {transaction.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className={`text-sm font-bold ${
                      transaction.type === 'Receita' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {transaction.type === 'Receita' ? '+' : '-'}{formatCurrency(transaction.value)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      transaction.status === 'Pago' ? 
                        'bg-blue-100 text-blue-800' : 
                        'bg-yellow-100 text-yellow-800'
                    }`}>
                      {transaction.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex justify-center space-x-2">
                      <button
                        onClick={() => onEdit(transaction)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Editar"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => onDelete(transaction.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Excluir"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Página {currentPage} de {totalPages}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Anterior
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const AccountsView = ({ accounts, onRefresh, onEdit, onDelete, onCreateNew }) => {
  return (
    <div className="space-y-6">
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
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Conta</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instituição</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Saldo Inicial</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Saldo Atual</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {accounts.map((account) => (
                <tr key={account.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div 
                        className="w-4 h-4 rounded-full mr-3"
                        style={{ backgroundColor: account.color_hex }}
                      ></div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{account.name}</div>
                        {account.type === 'Cartão de Crédito' && account.credit_limit && (
                          <div className="text-sm text-gray-500">
                            Limite: {formatCurrency(account.credit_limit)}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                      {account.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {account.institution || 'Não informado'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {formatCurrency(account.initial_balance)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className={`text-sm font-bold ${
                      account.current_balance >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(account.current_balance)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex justify-center space-x-2">
                      <button
                        onClick={() => onEdit(account)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Editar conta"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => onDelete(account.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Excluir conta"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {accounts.length === 0 && (
          <div className="text-center py-12">
            <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">Nenhuma conta cadastrada</p>
            <button
              onClick={onCreateNew}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Criar sua primeira conta
            </button>
          </div>
        )}
      </div>

      {/* Account Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Resumo por Tipo</h3>
          <div className="space-y-3">
            {[...new Set(accounts.map(a => a.type))].map(type => {
              const typeAccounts = accounts.filter(a => a.type === type);
              const totalBalance = typeAccounts.reduce((sum, acc) => sum + acc.current_balance, 0);
              
              return (
                <div key={type} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{type}</span>
                  <span className="text-sm font-medium">{formatCurrency(totalBalance)}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Por Instituição</h3>
          <div className="space-y-3">
            {[...new Set(accounts.map(a => a.institution).filter(Boolean))].map(institution => {
              const instAccounts = accounts.filter(a => a.institution === institution);
              const totalBalance = instAccounts.reduce((sum, acc) => sum + acc.current_balance, 0);
              
              return (
                <div key={institution} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{institution}</span>
                  <span className="text-sm font-medium">{formatCurrency(totalBalance)}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Estatísticas</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total de Contas</span>
              <span className="text-sm font-medium">{accounts.length}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Saldo Médio</span>
              <span className="text-sm font-medium">
                {accounts.length > 0 ? formatCurrency(
                  accounts.reduce((sum, acc) => sum + acc.current_balance, 0) / accounts.length
                ) : formatCurrency(0)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Contas Positivas</span>
              <span className="text-sm font-medium">
                {accounts.filter(a => a.current_balance > 0).length} de {accounts.length}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Goals View Component
const GoalsView = ({ goals, goalsStats, onRefresh, onCreateNew, onEdit, onDelete, onContribute }) => {
  const getGoalProgress = (goal) => {
    const percentage = goal.target_amount > 0 ? (goal.current_amount / goal.target_amount) * 100 : 0;
    return Math.min(percentage, 100);
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 100) return 'bg-green-500';
    if (percentage >= 75) return 'bg-blue-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-gray-300';
  };

  const getDaysRemaining = (targetDate) => {
    const today = new Date();
    const target = new Date(targetDate);
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'Alta': return 'text-red-600 bg-red-100';
      case 'Média': return 'text-yellow-600 bg-yellow-100';
      case 'Baixa': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* Goals Statistics */}
      {goalsStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white">
            <h3 className="text-sm font-medium text-blue-100 mb-2">Total de Metas</h3>
            <p className="text-3xl font-bold">{goalsStats.total_goals}</p>
            <p className="text-sm text-blue-200 mt-1">{goalsStats.active_goals} ativas</p>
          </div>
          
          <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl shadow-lg p-6 text-white">
            <h3 className="text-sm font-medium text-green-100 mb-2">Metas Atingidas</h3>
            <p className="text-3xl font-bold">{goalsStats.achieved_goals}</p>
            <p className="text-sm text-green-200 mt-1">
              {goalsStats.total_goals > 0 ? Math.round((goalsStats.achieved_goals / goalsStats.total_goals) * 100) : 0}% completas
            </p>
          </div>
          
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
            <h3 className="text-sm font-medium text-purple-100 mb-2">Total Poupado</h3>
            <p className="text-3xl font-bold">{formatCurrency(goalsStats.total_saved_amount)}</p>
            <p className="text-sm text-purple-200 mt-1">De {formatCurrency(goalsStats.total_target_amount)}</p>
          </div>
          
          <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl shadow-lg p-6 text-white">
            <h3 className="text-sm font-medium text-orange-100 mb-2">Progresso Geral</h3>
            <p className="text-3xl font-bold">{goalsStats.overall_progress.toFixed(1)}%</p>
            <p className="text-sm text-orange-200 mt-1">Das suas metas</p>
          </div>
        </div>
      )}

      {/* Goals Management */}
      <div className="bg-white rounded-xl shadow-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Suas Metas Financeiras</h2>
          <button
            onClick={onCreateNew}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus size={16} />
            Nova Meta
          </button>
        </div>

        <div className="p-6">
          {goals.length === 0 ? (
            <div className="text-center py-12">
              <DollarSign className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma meta definida</h3>
              <p className="text-gray-500 mb-6">
                Defina metas financeiras para alcançar seus objetivos mais facilmente!
              </p>
              <button
                onClick={onCreateNew}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Criar sua primeira meta
              </button>
            </div>
          ) : (
            <p className="text-gray-500">Metas carregadas: {goals.length}</p>
          )}
        </div>
      </div>
    </div>
  );
};

const BudgetsView = ({ budgets, categories, summary, onRefresh, onCreateNew, onEdit, onDelete }) => {
  const currentMonth = new Date().toISOString().slice(0, 7);

  const getBudgetProgress = (budget) => {
    const spent = summary?.expense_by_category?.[getCategoryName(budget.category_id)] || 0;
    const percentage = budget.budget_amount > 0 ? (spent / budget.budget_amount) * 100 : 0;
    return { spent, percentage: Math.min(percentage, 100) };
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(c => c.id === categoryId);
    return category?.name || 'Categoria não encontrada';
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 100) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getProgressTextColor = (percentage) => {
    if (percentage >= 100) return 'text-red-600';
    if (percentage >= 80) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Gerenciar Orçamentos</h2>
          <button
            onClick={onCreateNew}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <Plus size={16} />
            Novo Orçamento
          </button>
        </div>

        <div className="p-6">
          {budgets.length === 0 ? (
            <div className="text-center py-12">
              <PiggyBank className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Nenhum orçamento definido</p>
              <button
                onClick={onCreateNew}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                Criar seu primeiro orçamento
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {budgets.map((budget) => {
                const progress = getBudgetProgress(budget);
                
                return (
                  <div key={budget.id} className="border rounded-xl p-6 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {getCategoryName(budget.category_id)}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {new Date(budget.month_year + '-01').toLocaleDateString('pt-BR', { 
                            month: 'long', 
                            year: 'numeric' 
                          })}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => onEdit(budget)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Editar orçamento"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => onDelete(budget.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Excluir orçamento"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Orçado:</span>
                        <span className="font-medium">{formatCurrency(budget.budget_amount)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Gasto:</span>
                        <span className={`font-medium ${getProgressTextColor(progress.percentage)}`}>
                          {formatCurrency(progress.spent)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Restante:</span>
                        <span className={`font-medium ${
                          budget.budget_amount - progress.spent >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(budget.budget_amount - progress.spent)}
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="mt-4">
                        <div className="flex justify-between text-xs text-gray-600 mb-2">
                          <span>Progresso</span>
                          <span>{progress.percentage.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`h-3 rounded-full transition-all duration-300 ${getProgressColor(progress.percentage)}`}
                            style={{ width: `${Math.min(progress.percentage, 100)}%` }}
                          ></div>
                        </div>
                      </div>

                      {/* Status Alert */}
                      {progress.percentage >= 100 && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                          <div className="flex items-center">
                            <Bell className="w-4 h-4 text-red-500 mr-2" />
                            <span className="text-sm text-red-700 font-medium">
                              Orçamento excedido!
                            </span>
                          </div>
                          <p className="text-xs text-red-600 mt-1">
                            Você ultrapassou o orçamento em {formatCurrency(progress.spent - budget.budget_amount)}
                          </p>
                        </div>
                      )}
                      
                      {progress.percentage >= 80 && progress.percentage < 100 && (
                        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <div className="flex items-center">
                            <Bell className="w-4 h-4 text-yellow-500 mr-2" />
                            <span className="text-sm text-yellow-700 font-medium">
                              Atenção: {progress.percentage.toFixed(1)}% do orçamento utilizado
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Budget Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Total Orçado</h3>
          <p className="text-3xl font-bold text-blue-600">
            {formatCurrency(budgets.reduce((sum, budget) => sum + budget.budget_amount, 0))}
          </p>
          <p className="text-sm text-gray-500 mt-1">Para este mês</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Total Gasto</h3>
          <p className="text-3xl font-bold text-red-600">
            {formatCurrency(summary?.monthly_expenses || 0)}
          </p>
          <p className="text-sm text-gray-500 mt-1">Este mês</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Orçamentos Ativos</h3>
          <p className="text-3xl font-bold text-green-600">{budgets.length}</p>
          <p className="text-sm text-gray-500 mt-1">Categorias com orçamento</p>
        </div>
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

// Enhanced Transaction Modal Component with Intelligence
const TransactionModal = ({ transaction, type, accounts, categories, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    description: transaction?.description || '',
    value: transaction?.value || '',
    type: type,
    transaction_date: transaction?.transaction_date ? 
      formatDateForInput(transaction.transaction_date) : 
      formatDateForInput(new Date()),
    account_id: transaction?.account_id || '',
    category_id: transaction?.category_id || '',
    observation: transaction?.observation || '',
    is_recurring: transaction?.is_recurring || false,
    recurrence_interval: transaction?.recurrence_interval || '',
    status: transaction?.status || 'Pago',
    file: null
  });

  const [recentDescriptions, setRecentDescriptions] = useState([]);
  const [showDescriptionSuggestions, setShowDescriptionSuggestions] = useState(false);
  const [suggestedCategory, setSuggestedCategory] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load recent descriptions on mount
  useEffect(() => {
    const loadRecentDescriptions = async () => {
      try {
        const response = await axios.get(`${API}/transactions/recent-descriptions`);
        setRecentDescriptions(response.data);
      } catch (error) {
        console.log('Failed to load recent descriptions');
      }
    };
    loadRecentDescriptions();
  }, []);

  // Intelligent category suggestion when description changes
  const handleDescriptionChange = async (value) => {
    setFormData({...formData, description: value});
    
    if (value.length > 2) {
      try {
        const response = await axios.post(`${API}/transactions/suggest-category`, {
          description: value,
          type: type
        });
        
        if (response.data.confidence === 'high') {
          setSuggestedCategory(response.data);
          // Auto-select if high confidence and no category selected
          if (!formData.category_id && response.data.category_id) {
            setFormData(prev => ({...prev, category_id: response.data.category_id}));
          }
        }
      } catch (error) {
        console.log('Category suggestion failed');
      }
    }
  };

  // Description autocomplete
  const filteredDescriptions = recentDescriptions.filter(desc => 
    desc.toLowerCase().includes(formData.description.toLowerCase()) && 
    desc !== formData.description
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const transactionData = {
        ...formData,
        transaction_date: new Date(formData.transaction_date).toISOString(),
        value: parseFloat(formData.value)
      };
      
      // Handle file upload if present
      if (formData.file) {
        const reader = new FileReader();
        reader.onload = () => {
          transactionData.file_data = reader.result; // Base64
          transactionData.file_name = formData.file.name;
          onCreate(transactionData);
        };
        reader.readAsDataURL(formData.file);
      } else {
        onCreate(transactionData);
      }
    } catch (error) {
      console.error('Transaction submission error:', error);
    } finally {
      setLoading(false);
    }
  };

  const relevantCategories = categories.filter(cat => cat.type === type);
  const recurrenceOptions = ['Diária', 'Semanal', 'Quinzenal', 'Mensal', 'Anual'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[95vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold">
            {transaction ? `Editar ${type}` : `Adicionar ${type}`}
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Description with Autocomplete */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Descrição * 
              {suggestedCategory && (
                <span className="text-xs text-green-600 ml-2">
                  (Categoria sugerida: {suggestedCategory.suggested_category})
                </span>
              )}
            </label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.description}
              onChange={(e) => handleDescriptionChange(e.target.value)}
              onFocus={() => setShowDescriptionSuggestions(true)}
              onBlur={() => setTimeout(() => setShowDescriptionSuggestions(false), 200)}
              placeholder={type === 'Receita' ? 'Ex: Salário, Freelance' : 'Ex: Supermercado, Restaurante'}
            />
            
            {/* Description Suggestions Dropdown */}
            {showDescriptionSuggestions && filteredDescriptions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-40 overflow-y-auto">
                {filteredDescriptions.slice(0, 5).map((desc, index) => (
                  <div
                    key={index}
                    className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm"
                    onClick={() => {
                      handleDescriptionChange(desc);
                      setShowDescriptionSuggestions(false);
                    }}
                  >
                    {desc}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Value and Date Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <label className="block text-sm font-medium text-gray-700 mb-2">Data da Transação *</label>
              <input
                type="date"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.transaction_date}
                onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
              />
            </div>
          </div>

          {/* Account and Category Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                    {account.name} ({account.type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Categoria *</label>
              <select
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.category_id}
                onChange={(e) => setFormData({...formData, category_id: e.target.value})}
              >
                <option value="">Selecione uma categoria</option>
                {relevantCategories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Status and Observations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Observações/Tags</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.observation}
                onChange={(e) => setFormData({...formData, observation: e.target.value})}
                placeholder="Ex: #viagem, nota fiscal"
              />
            </div>
          </div>

          {/* Recurrence Options */}
          <div className="border-t pt-4">
            <div className="flex items-center mb-3">
              <input
                type="checkbox"
                id="recurring"
                className="mr-2"
                checked={formData.is_recurring}
                onChange={(e) => setFormData({...formData, is_recurring: e.target.checked})}
              />
              <label htmlFor="recurring" className="text-sm font-medium text-gray-700">
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
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Anexar Comprovante</label>
            <input
              type="file"
              accept="image/*,.pdf"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              onChange={(e) => setFormData({...formData, file: e.target.files[0]})}
            />
            <p className="text-xs text-gray-500 mt-1">Formatos aceitos: JPG, PNG, PDF (máx. 5MB)</p>
          </div>

          {/* Form Buttons */}
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
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Salvando...' : (transaction ? 'Atualizar' : 'Criar')} {type}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
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
const BudgetModal = ({ budget, categories, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    category_id: budget?.category_id || '',
    budget_amount: budget?.budget_amount || 0,
    month_year: budget?.month_year || new Date().toISOString().slice(0, 7) // YYYY-MM format
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
        <h3 className="text-xl font-semibold mb-6">
          {budget ? 'Editar Orçamento' : 'Definir Orçamento'}
        </h3>
        
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
              {budget ? 'Atualizar' : 'Definir'} Orçamento
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

// Goal Modal Component
const GoalModal = ({ goal, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: goal?.name || '',
    description: goal?.description || '',
    target_amount: goal?.target_amount || '',
    current_amount: goal?.current_amount || 0,
    target_date: goal?.target_date ? formatDateForInput(goal.target_date) : '',
    category: goal?.category || 'Emergência',
    priority: goal?.priority || 'Média',
    auto_contribution: goal?.auto_contribution || ''
  });

  const goalCategories = ['Emergência', 'Casa Própria', 'Viagem', 'Aposentadoria', 'Outros'];
  const priorities = ['Alta', 'Média', 'Baixa'];

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const goalData = {
      name: formData.name,
      description: formData.description,
      target_amount: parseFloat(formData.target_amount),
      current_amount: parseFloat(formData.current_amount) || 0,
      target_date: new Date(formData.target_date).toISOString(),
      category: formData.category,
      priority: formData.priority,
      auto_contribution: formData.auto_contribution ? parseFloat(formData.auto_contribution) : null
    };

    onCreate(goalData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 rounded-t-xl">
          <h2 className="text-xl font-semibold text-gray-900">
            {goal ? 'Editar Meta' : 'Nova Meta Financeira'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nome da Meta *</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="Ex: Casa Própria, Viagem dos Sonhos"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Descrição</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Descrição detalhada da sua meta"
              rows="3"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valor Alvo *</label>
              <input
                type="number"
                step="0.01"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.target_amount}
                onChange={(e) => setFormData({...formData, target_amount: e.target.value})}
                placeholder="0,00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valor Atual</label>
              <input
                type="number"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.current_amount}
                onChange={(e) => setFormData({...formData, current_amount: e.target.value})}
                placeholder="0,00"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Data Alvo *</label>
            <input
              type="date"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.target_date}
              onChange={(e) => setFormData({...formData, target_date: e.target.value})}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Categoria *</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
              >
                {goalCategories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Prioridade</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: e.target.value})}
              >
                {priorities.map(priority => (
                  <option key={priority} value={priority}>{priority}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Contribuição Automática Mensal</label>
            <input
              type="number"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.auto_contribution}
              onChange={(e) => setFormData({...formData, auto_contribution: e.target.value})}
              placeholder="0,00 (opcional)"
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
              {goal ? 'Atualizar' : 'Criar'} Meta
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Contribute Modal Component
const ContributeModal = ({ goal, onClose, onContribute }) => {
  const [amount, setAmount] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const contributionAmount = parseFloat(amount);
    if (contributionAmount > 0) {
      onContribute(goal.id, contributionAmount);
    }
  };

  const remainingAmount = (goal?.target_amount || 0) - (goal?.current_amount || 0);
  const progressPercentage = goal?.target_amount > 0 ? (goal?.current_amount / goal?.target_amount) * 100 : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
        <div className="px-6 py-4 border-b border-gray-200 rounded-t-xl">
          <h2 className="text-xl font-semibold text-gray-900">Contribuir para Meta</h2>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">{goal?.name}</h3>
            <p className="text-sm text-gray-600 mb-4">{goal?.description}</p>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span>Progresso atual:</span>
                <span>{progressPercentage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                <div
                  className="bg-blue-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                ></div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Valor atual:</span>
                  <p className="font-medium">{formatCurrency(goal?.current_amount || 0)}</p>
                </div>
                <div>
                  <span className="text-gray-600">Valor alvo:</span>
                  <p className="font-medium">{formatCurrency(goal?.target_amount || 0)}</p>
                </div>
                <div>
                  <span className="text-gray-600">Restante:</span>
                  <p className="font-medium text-blue-600">{formatCurrency(remainingAmount)}</p>
                </div>
                <div>
                  <span className="text-gray-600">Data alvo:</span>
                  <p className="font-medium">{goal?.target_date ? formatDate(goal.target_date) : 'N/A'}</p>
                </div>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valor da Contribuição *</label>
              <input
                type="number"
                step="0.01"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0,00"
                min="0.01"
                max={remainingAmount}
              />
              <p className="text-xs text-gray-500 mt-1">
                Valor máximo: {formatCurrency(remainingAmount)}
              </p>
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
                disabled={!amount || parseFloat(amount) <= 0}
              >
                Contribuir
              </button>
            </div>
          </form>
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