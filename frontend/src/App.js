import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";
import { Toaster, toast } from 'react-hot-toast';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import { Plus, TrendingUp, TrendingDown, CreditCard, PiggyBank, DollarSign, FileText, Settings, Bell, Calendar, Filter, Download, Upload, Edit, Trash2, Eye, EyeOff, Target, Clock, CheckCircle, Package, ShoppingCart, BarChart3, AlertTriangle, Search } from 'lucide-react';
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
// Brazilian currency formatting functions
const formatBrazilianCurrency = (value) => {
  // Remove all non-digit characters
  let cleanValue = value.toString().replace(/\D/g, '');
  if (!cleanValue) return '';
  
  // Add leading zeros if necessary to handle cents
  while (cleanValue.length < 3) {
    cleanValue = '0' + cleanValue;
  }
  
  // Insert decimal separator
  const integerPart = cleanValue.slice(0, -2) || '0';
  const decimalPart = cleanValue.slice(-2);
  
  // Format as currency
  const numericValue = parseFloat(`${integerPart}.${decimalPart}`);
  return numericValue.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
};

const parseBrazilianCurrency = (formattedValue) => {
  // Remove currency symbol and convert comma to dot
  const cleanValue = formattedValue
    .replace(/R\$\s?/, '')
    .replace(/\./g, '')  // Remove thousands separator
    .replace(',', '.');   // Convert decimal separator
  
  const numericValue = parseFloat(cleanValue);
  return isNaN(numericValue) ? 0 : numericValue;
};

// Format currency (Brazilian Real)
const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value || 0);
};

// Format date (Brazilian format)
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR');
};

const formatDateForInput = (date) => {
  return new Date(date).toISOString().split('T')[0];
};

// Enhanced Login Component
// Password validation component
const PasswordInput = ({ value, onChange, placeholder = "Sua senha", required = false, confirm = false, confirmValue = '', className = "" }) => {
  const [isValid, setIsValid] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const validatePassword = (password) => {
    if (!password && required) {
      setErrorMessage('Senha é obrigatória');
      setIsValid(false);
      return false;
    }
    
    if (password && password.length < 6) {
      setErrorMessage('Senha deve ter pelo menos 6 caracteres');
      setIsValid(false);
      return false;
    }
    
    if (confirm && password !== confirmValue) {
      setErrorMessage('Senhas não coincidem');
      setIsValid(false);
      return false;
    }
    
    setErrorMessage('');
    setIsValid(true);
    return true;
  };

  const handleChange = (e) => {
    const passwordValue = e.target.value;
    onChange(passwordValue);
    
    // Validate in real time
    if (passwordValue || confirm) {
      validatePassword(passwordValue);
    } else {
      setIsValid(true);
      setErrorMessage('');
    }
  };

  const handleBlur = () => {
    if (value || confirm) {
      validatePassword(value);
    }
  };

  return (
    <div>
      <div className="relative">
        <input
          type={showPassword ? "text" : "password"}
          className={`w-full px-4 py-3 pr-12 border ${isValid ? 'border-gray-300' : 'border-red-500'} rounded-lg focus:outline-none ${isValid ? 'focus:border-blue-500 focus:ring-blue-200' : 'focus:border-red-500 focus:ring-red-200'} focus:ring-2 transition-all ${className}`}
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          required={required}
        />
        <button
          type="button"
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
          onClick={() => setShowPassword(!showPassword)}
        >
          {showPassword ? '🙈' : '👁️'}
        </button>
      </div>
      {!isValid && errorMessage && (
        <p className="text-red-500 text-sm mt-1">⚠️ {errorMessage}</p>
      )}
    </div>
  );
};

// Email validation component
const EmailInput = ({ value, onChange, placeholder = "seu@email.com", required = false, className = "" }) => {
  const [isValid, setIsValid] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValidFormat = emailRegex.test(email);
    
    if (!email && required) {
      setErrorMessage('Email é obrigatório');
      setIsValid(false);
      return false;
    }
    
    if (email && !isValidFormat) {
      setErrorMessage('Digite um email válido (exemplo@dominio.com)');
      setIsValid(false);
      return false;
    }
    
    setErrorMessage('');
    setIsValid(true);
    return true;
  };

  const handleChange = (e) => {
    const emailValue = e.target.value;
    onChange(emailValue);
    
    // Validate in real time
    if (emailValue) {
      validateEmail(emailValue);
    } else {
      setIsValid(true);
      setErrorMessage('');
    }
  };

  const handleBlur = () => {
    if (value) {
      validateEmail(value);
    }
  };

  return (
    <div>
      <input
        type="email"
        className={`w-full px-3 py-2 border ${isValid ? 'border-gray-300' : 'border-red-500'} rounded-lg focus:outline-none ${isValid ? 'focus:border-blue-500 focus:ring-blue-200' : 'focus:border-red-500 focus:ring-red-200'} focus:ring-2 transition-all ${className}`}
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        onBlur={handleBlur}
        required={required}
      />
      {!isValid && errorMessage && (
        <p className="text-red-500 text-sm mt-1">⚠️ {errorMessage}</p>
      )}
    </div>
  );
};

// Brazilian Currency Input Component
const BrazilianCurrencyInput = ({ value, onChange, placeholder = "R$ 0,00", required = false, className = "" }) => {
  const [displayValue, setDisplayValue] = useState('');

  useEffect(() => {
    if (value && value > 0) {
      // Format existing value for display
      const formatted = value.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
      });
      setDisplayValue(formatted);
    } else {
      setDisplayValue('');
    }
  }, [value]);

  const handleInputChange = (e) => {
    let inputValue = e.target.value;
    
    // Remove all non-digit characters
    const digitsOnly = inputValue.replace(/\D/g, '');
    
    if (!digitsOnly) {
      setDisplayValue('');
      onChange(0);
      return;
    }
    
    // Convert digits to number (treating as cents)
    const numericValue = parseFloat(digitsOnly) / 100;
    
    // Format for display
    const formatted = numericValue.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
    
    setDisplayValue(formatted);
    onChange(numericValue);
  };

  return (
    <input
      type="text"
      className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all ${className}`}
      placeholder={placeholder}
      value={displayValue}
      onChange={handleInputChange}
      required={required}
    />
  );
};

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
          setLoading(false);
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
            <EmailInput
              value={formData.email}
              onChange={(email) => setFormData({...formData, email: email})}
              placeholder="seu@email.com"
              required
              className="px-4 py-3"
            />
          </div>
          
          {!showForgotPassword && (
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">Senha</label>
              <PasswordInput
                value={formData.password}
                onChange={(password) => setFormData({...formData, password: password})}
                placeholder="Sua senha"
                required
              />
            </div>
          )}

          {!isLogin && !showForgotPassword && (
            <div>
              <label className="block text-gray-700 text-sm font-medium mb-2">Confirmar Senha</label>
              <PasswordInput
                value={formData.confirmPassword}
                onChange={(password) => setFormData({...formData, confirmPassword: password})}
                placeholder="Confirme sua senha"
                confirm={true}
                confirmValue={formData.password}
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
  const [reportType, setReportType] = useState('overview'); // For enhanced reports

  // 🧠 IA States
  const [showAIChat, setShowAIChat] = useState(false);
  const [showAIInsights, setShowAIInsights] = useState(false);
  const [aiInsights, setAIInsights] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  
  // Dashboard customization
  const toggleDashboardWidget = (widgetId) => {
    setDashboardWidgets(prev => 
      prev.includes(widgetId) 
        ? prev.filter(id => id !== widgetId)
        : [...prev, widgetId]
    );
    
    // Save preferences to localStorage
    const newWidgets = dashboardWidgets.includes(widgetId) 
      ? dashboardWidgets.filter(id => id !== widgetId)
      : [...dashboardWidgets, widgetId];
    localStorage.setItem('dashboardWidgets', JSON.stringify(newWidgets));
  };

  // Global search functionality
  const handleGlobalSearch = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const results = [];
      
      // Search in transactions
      const matchingTransactions = transactions.filter(t => 
        t.description?.toLowerCase().includes(query.toLowerCase()) ||
        t.category?.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 3);
      
      if (matchingTransactions.length > 0) {
        results.push({
          category: 'Transações',
          items: matchingTransactions.map(t => ({
            id: t.id,
            title: t.description,
            subtitle: `${t.category} - ${formatCurrency(t.amount)}`,
            action: () => setActiveView('transactions')
          }))
        });
      }

      // Search in accounts
      const matchingAccounts = accounts.filter(a => 
        a.name?.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 2);
      
      if (matchingAccounts.length > 0) {
        results.push({
          category: 'Contas',
          items: matchingAccounts.map(a => ({
            id: a.id,
            title: a.name,
            subtitle: `Saldo: ${formatCurrency(a.balance)}`,
            action: () => setActiveView('accounts')
          }))
        });
      }

      // Search modules
      const modules = [
        { id: 'dashboard', name: 'Dashboard', icon: '📊' },
        { id: 'transactions', name: 'Transações', icon: '💳' },
        { id: 'accounts', name: 'Contas', icon: '🏦' },
        { id: 'goals', name: 'Metas', icon: '🎯' },
        { id: 'budgets', name: 'Orçamentos', icon: '📈' },
        { id: 'petshop', name: 'Pet Shop', icon: '🐾' },
        { id: 'contracts', name: 'Contratos', icon: '🏠' },
        { id: 'credit-cards', name: 'Cartões', icon: '💳' }
      ];

      const matchingModules = modules.filter(m => 
        m.name.toLowerCase().includes(query.toLowerCase())
      );

      if (matchingModules.length > 0) {
        results.push({
          category: 'Módulos',
          items: matchingModules.map(m => ({
            id: m.id,
            title: m.name,
            subtitle: `Ir para ${m.name}`,
            icon: m.icon,
            action: () => {
              setActiveView(m.id);
              setShowSearchBar(false);
              setSearchQuery('');
            }
          }))
        });
      }

      setSearchResults(results);
    } catch (error) {
      console.error('Erro na busca global:', error);
    }
  };

  // Debounced search
  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      handleGlobalSearch(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, transactions, accounts]);

  // Load dashboard preferences
  React.useEffect(() => {
    const savedWidgets = localStorage.getItem('dashboardWidgets');
    if (savedWidgets) {
      setDashboardWidgets(JSON.parse(savedWidgets));
    }
    
    const sidebarState = localStorage.getItem('sidebarCollapsed');
    if (sidebarState !== null) {
      setSidebarCollapsed(JSON.parse(sidebarState));
    }
  }, []);

  // 🏠 Consortium States
  const [showConsortiumModal, setShowConsortiumModal] = useState(false);
  const [showConsortiumDetails, setShowConsortiumDetails] = useState(false);
  const [consortiums, setConsortiums] = useState([]);
  const [selectedConsortium, setSelectedConsortium] = useState(null);

  // 💳 Credit Card Invoice States
  const [showCreditCardModal, setShowCreditCardModal] = useState(false);
  const [creditCardInvoices, setCreditCardInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);

  // 👤 User Profile States
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [profileData, setProfileData] = useState({
    name: '',
    email: ''
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  // 📄 File Import States
  const [importStep, setImportStep] = useState('upload'); // 'upload', 'preview', 'confirming'
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [importSession, setImportSession] = useState(null);
  const [importPreview, setImportPreview] = useState([]);
  const [importLoading, setImportLoading] = useState(false);
  const [selectedTransactions, setSelectedTransactions] = useState([]);

  // Mobile menu state
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  // Sidebar state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showSearchBar, setShowSearchBar] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  // Dashboard customization state
  const [dashboardWidgets, setDashboardWidgets] = useState([
    'recent_transactions',
    'total_balance', 
    'budgets_overview',
    'petshop_summary',
    'alerts'
  ]);
  const [contracts, setContracts] = useState([]);
  const [showContractModal, setShowContractModal] = useState(false);
  const [editingContract, setEditingContract] = useState(null);

  // 🐾 Pet Shop states
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [currentReceipt, setCurrentReceipt] = useState(null);
  const [contractsLoading, setContractsLoading] = useState(false);
  const [contractFilters, setContractFilters] = useState({
    tipo: '',
    status: ''
  });
  const [contractStats, setContractStats] = useState({});

  // ✨ Biblical Messages and Motivational System
  const [dailyMessage, setDailyMessage] = useState(null);
  
  const biblicalMessages = [
    {
      verse: "Filipenses 4:19",
      message: "O meu Deus suprirá todas as vossas necessidades segundo as suas riquezas na glória em Cristo Jesus.",
      category: "provisão"
    },
    {
      verse: "Provérbios 21:5",
      message: "Os planos do diligente tendem à abundância, mas todo apressado tende à pobreza.",
      category: "planejamento"
    },
    {
      verse: "1 Timóteo 6:10",
      message: "Porque o amor ao dinheiro é a raiz de toda espécie de males; e nessa cobiça alguns se desviaram da fé.",
      category: "sabedoria"
    },
    {
      verse: "Provérbios 13:11",
      message: "A riqueza de procedência vã diminuirá, mas quem ajunta à força do trabalho aumentará.",
      category: "trabalho"
    },
    {
      verse: "Lucas 14:28",
      message: "Pois qual de vós, querendo edificar uma torre, não se assenta primeiro a fazer as contas dos gastos?",
      category: "planejamento"
    },
    {
      verse: "Malaquias 3:10",
      message: "Trazei todos os dízimos à casa do tesouro... e provai-me nisto, se eu não vos abrir as janelas do céu.",
      category: "fidelidade"
    },
    {
      verse: "Provérbios 27:23",
      message: "Procura conhecer o estado das tuas ovelhas, e cuida dos teus rebanhos.",
      category: "administração"
    },
    {
      verse: "Hebreus 13:5",
      message: "Seja a vossa vida sem avareza, contentando-vos com o que tendes.",
      category: "contentamento"
    },
    {
      verse: "2 Coríntios 9:7",
      message: "Cada um contribua segundo propôs no seu coração; não com tristeza ou por necessidade.",
      category: "generosidade"
    },
    {
      verse: "Provérbios 22:7",
      message: "O rico domina sobre os pobres, e o que toma emprestado é servo do que empresta.",
      category: "dívidas"
    },
    {
      verse: "Eclesiastes 11:2",
      message: "Reparte com sete e ainda com oito, porque não sabes que mal haverá sobre a terra.",
      category: "diversificação"
    },
    {
      verse: "Mateus 6:26",
      message: "Olhai para as aves do céu, que nem semeiam, nem segam... vosso Pai celestial as alimenta.",
      category: "confiança"
    }
  ];

  const motivationalMessages = [
    {
      message: "Cada real economizado hoje é um passo em direção à sua liberdade financeira de amanhã.",
      category: "economia"
    },
    {
      message: "Controlar suas finanças é controlar seu futuro. Você está no caminho certo!",
      category: "controle"
    },
    {
      message: "Pequenos passos consistentes levam a grandes transformações financeiras.",
      category: "persistência"
    },
    {
      message: "Sua disciplina de hoje será a abundância de amanhã.",
      category: "disciplina"
    },
    {
      message: "Investir em conhecimento financeiro é o melhor investimento que você pode fazer.",
      category: "educação"
    },
    {
      message: "Cada transação registrada é um ato de amor próprio e responsabilidade.",
      category: "organização"
    },
    {
      message: "Você não está apenas gerenciando dinheiro, está construindo um futuro próspero.",
      category: "visão"
    },
    {
      message: "A prosperidade começa com uma decisão: tomar controle das suas finanças.",
      category: "decisão"
    }
  ];

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
      
  // 🧠 Load AI Insights
  try {
    const aiInsightsRes = await axios.get(`${API}/ai/insights`);
    setAIInsights(aiInsightsRes.data);
  } catch (aiError) {
    console.log('AI Insights loading failed, continuing without AI');
    setAIInsights([]);
  }

  // 🏠 Load Consortiums  
  try {
    const consortiumsRes = await axios.get(`${API}/consortiums`);
    setConsortiums(consortiumsRes.data);
  } catch (consortiumError) {
    console.log('Consortiums loading failed, continuing without consortiums');
    setConsortiums([]);
  }

  // 📊 Load Hierarchical Categories
  try {
    const hierarchicalCategoriesRes = await axios.get(`${API}/categories/hierarchical`);
    setCategories(hierarchicalCategoriesRes.data);
  } catch (categoryError) {
    console.log('Hierarchical categories loading failed, using simple categories');
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

  // State for fixed quick actions
  const [showFixedActions, setShowFixedActions] = useState(false);

  // Effect to handle scroll and show/hide fixed actions
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      // Show fixed actions when scrolled down more than 200px and on dashboard
      if (scrollY > 200 && activeView === 'dashboard') {
        setShowFixedActions(true);
      } else {
        setShowFixedActions(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [activeView]);

  useEffect(() => {
    loadDashboard();
  }, []);

  // ============================================================================
  // 🧠 FUNÇÕES DE IA
  // ============================================================================

  const sendChatMessage = async (message) => {
    try {
      const response = await axios.post(`${API}/ai/chat`, { message });
      const aiResponse = response.data.response;
      
      setChatMessages(prev => [...prev, 
        { type: 'user', message, timestamp: new Date() },
        { type: 'ai', message: aiResponse, timestamp: new Date() }
      ]);
      
      return aiResponse;
    } catch (error) {
      toast.error('Erro ao comunicar com IA: ' + (error.response?.data?.detail || 'Erro desconhecido'));
      return 'Desculpe, ocorreu um erro. Tente novamente.';
    }
  };

  const loadAIInsights = async () => {
    try {
      const response = await axios.get(`${API}/ai/insights`);
      setAIInsights(response.data);
    } catch (error) {
      console.error('Erro ao carregar insights de IA:', error);
    }
  };

  const classifyTransaction = async (description) => {
    try {
      const response = await axios.post(`${API}/ai/classify-transaction`, { description });
      return response.data;
    } catch (error) {
      console.error('Erro na classificação automática:', error);
      return null;
    }
  };

  // ============================================================================
  // 💳 FUNÇÕES DE CARTÃO DE CRÉDITO
  // ============================================================================

  // Load credit card invoices
  const loadCreditCardInvoices = async () => {
    setLoadingInvoices(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/credit-cards/invoices`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCreditCardInvoices(data.invoices || []);
      } else {
        toast.error('Erro ao carregar faturas do cartão');
      }
    } catch (error) {
      console.error('Error loading credit card invoices:', error);
      toast.error('Erro ao carregar faturas');
    }
    setLoadingInvoices(false);
  };

  // Generate credit card invoices
  const generateCreditCardInvoices = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/credit-cards/generate-invoices`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        loadCreditCardInvoices(); // Reload invoices
      } else {
        toast.error('Erro ao gerar faturas');
      }
    } catch (error) {
      console.error('Error generating invoices:', error);
      toast.error('Erro ao gerar faturas');
    }
  };

  // Pay credit card invoice
  const payCreditCardInvoice = async (invoiceId, paymentAmount) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/credit-cards/invoices/${invoiceId}/pay`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ payment_amount: paymentAmount })
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        loadCreditCardInvoices(); // Reload invoices
        loadDashboard(); // Reload dashboard to update balances
      } else {
        toast.error('Erro ao pagar fatura');
      }
    } catch (error) {
      console.error('Error paying invoice:', error);
      toast.error('Erro ao pagar fatura');
    }
  };

  // ============================================================================
  // 🏠 FUNÇÕES DE CONSÓRCIO  
  // ============================================================================

  const handleCreateConsortium = async (formData) => {
    try {
      const response = await axios.post(`${API}/consortiums`, formData);
      await loadDashboard();
      toast.success('Consórcio criado com sucesso!');
      setShowConsortiumModal(false);
    } catch (error) {
      toast.error('Erro ao criar consórcio: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleConsortiumPayment = async (consortiumId, paymentData) => {
    try {
      await axios.post(`${API}/consortiums/${consortiumId}/payment`, paymentData);
      await loadDashboard();
      toast.success('Pagamento registrado com sucesso!');
    } catch (error) {
      toast.error('Erro ao registrar pagamento: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const handleMarkContemplation = async (consortiumId) => {
    try {
      await axios.post(`${API}/consortiums/${consortiumId}/contemplation`, {
        contemplation_type: "Sorteio",
        contemplation_date: new Date().toISOString()
      });
      await loadDashboard();
      toast.success('Consórcio marcado como contemplado!');
    } catch (error) {
      toast.error('Erro ao marcar contemplação: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  const loadConsortiumSummary = async (consortiumId) => {
    try {
      const response = await axios.get(`${API}/consortiums/${consortiumId}/summary`);
      setSelectedConsortium(response.data);
      setShowConsortiumDetails(true);
    } catch (error) {
      toast.error('Erro ao carregar detalhes do consórcio: ' + (error.response?.data?.detail || 'Erro desconhecido'));
    }
  };

  // ============================================================================
  // 👤 FUNÇÕES DE PERFIL DE USUÁRIO  
  // ============================================================================

  const loadProfile = async () => {
    try {
      const response = await axios.get(`${API}/users/profile`);
      setProfileData({
        name: response.data.name,
        email: response.data.email
      });
    } catch (error) {
      console.error('Error loading profile:', error);
      toast.error('Erro ao carregar perfil');
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/users/profile`, profileData);
      toast.success('Perfil atualizado com sucesso!');
      setShowProfileModal(false);
      // Reload dashboard to get updated user info
      await loadDashboard();
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar perfil');
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Nova senha e confirmação não coincidem');
      return;
    }
    try {
      await axios.put(`${API}/users/profile/password`, passwordData);
      toast.success('Senha alterada com sucesso!');
      setShowPasswordModal(false);
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error(error.response?.data?.detail || 'Erro ao alterar senha');
    }
  };

  const openProfileModal = () => {
    loadProfile();
    setShowProfileModal(true);
  };

  const openPasswordModal = () => {
    setPasswordData({
      current_password: '',
      new_password: '',
      confirm_password: ''
    });
    setShowPasswordModal(true);
  };

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
    const account = accounts.find(acc => acc.id === accountId);
    const accountName = account ? account.name : 'esta conta';
    
    if (!window.confirm(`⚠️ ATENÇÃO: Tem certeza que deseja excluir a conta "${accountName}"?\n\n🗑️ Esta ação irá:\n• Excluir a conta permanentemente\n• Remover TODAS as transações associadas\n• Esta operação NÃO pode ser desfeita\n\nDigite OK para confirmar a exclusão.`)) {
      return;
    }
    
    try {
      const response = await axios.delete(`${API}/accounts/${accountId}`);
      await loadDashboard();
      
      const message = response.data.transactions_deleted > 0 
        ? `Conta "${accountName}" excluída com sucesso! ${response.data.transactions_deleted} transações também foram removidas.`
        : `Conta "${accountName}" excluída com sucesso!`;
        
      toast.success(message);
    } catch (error) {
      console.error('Delete account error:', error);
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

  // 📄 File Import Functions
  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) {
      toast.error('Por favor, selecione pelo menos um arquivo');
      return;
    }

    setImportLoading(true);
    const formData = new FormData();
    
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API}/import/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const { session_id, preview_data } = response.data;
      setImportSession(session_id);
      setImportPreview(preview_data || []);
      setSelectedTransactions(preview_data || []);
      setImportStep('preview');
      
      toast.success(`${Array.from(files).length} arquivo(s) processado(s) com sucesso!`);
    } catch (error) {
      console.error('Erro no upload:', error);
      toast.error(error.response?.data?.detail || 'Erro ao fazer upload dos arquivos');
    } finally {
      setImportLoading(false);
    }
  };

  const handleImportConfirm = async () => {
    if (!importSession || selectedTransactions.length === 0) {
      toast.error('Nenhuma transação selecionada para importação');
      return;
    }

    setImportLoading(true);
    setImportStep('confirming');

    try {
      const response = await axios.post(`${API}/import/confirm`, {
        session_id: importSession,
        selected_transactions: selectedTransactions
      });

      toast.success(response.data.message || 'Importação concluída com sucesso!');
      
      // Reset import state and reload transactions
      setImportStep('upload');
      setImportSession(null);
      setImportPreview([]);
      setSelectedTransactions([]);
      setSelectedFiles([]);
      
      // Reload data
      await loadDashboard();
      
    } catch (error) {
      console.error('Erro na confirmação:', error);
      toast.error(error.response?.data?.detail || 'Erro ao confirmar importação');
      setImportStep('preview'); // Return to preview on error
    } finally {
      setImportLoading(false);
    }
  };

  const toggleTransactionSelection = (transaction) => {
    const isSelected = selectedTransactions.some(t => 
      t.descricao === transaction.descricao && 
      t.valor === transaction.valor && 
      t.data === transaction.data
    );

    if (isSelected) {
      setSelectedTransactions(selectedTransactions.filter(t => 
        !(t.descricao === transaction.descricao && 
          t.valor === transaction.valor && 
          t.data === transaction.data)
      ));
    } else {
      setSelectedTransactions([...selectedTransactions, transaction]);
    }
  };

  const resetImport = () => {
    setImportStep('upload');
    setImportSession(null);
    setImportPreview([]);
    setSelectedTransactions([]);
    setSelectedFiles([]);
  };

  // 🏠 Contracts Functions
  const loadContracts = async () => {
    setContractsLoading(true);
    try {
      const params = new URLSearchParams();
      if (contractFilters.tipo) params.append('tipo', contractFilters.tipo);
      if (contractFilters.status) params.append('status', contractFilters.status);
      
      const response = await axios.get(`${API}/contratos?${params.toString()}`);
      setContracts(response.data);
    } catch (error) {
      console.error('Erro ao carregar contratos:', error);
      toast.error('Erro ao carregar contratos');
    } finally {
      setContractsLoading(false);
    }
  };

  const loadContractStats = async () => {
    try {
      const response = await axios.get(`${API}/contratos/statistics`);
      setContractStats(response.data);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const handleCreateContract = async (contractData) => {
    try {
      const response = await axios.post(`${API}/contratos`, contractData);
      toast.success(response.data.message);
      setShowContractModal(false);
      setEditingContract(null);
      await loadContracts();
      await loadContractStats();
    } catch (error) {
      console.error('Erro ao criar contrato:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar contrato');
    }
  };

  const handleUpdateContract = async (contractId, contractData) => {
    try {
      const response = await axios.put(`${API}/contratos/${contractId}`, contractData);
      toast.success(response.data.message);
      setShowContractModal(false);
      setEditingContract(null);
      await loadContracts();
      await loadContractStats();
    } catch (error) {
      console.error('Erro ao atualizar contrato:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar contrato');
    }
  };

  const handleDeleteContract = async (contractId) => {
    if (window.confirm('Tem certeza que deseja excluir este contrato?')) {
      try {
        const response = await axios.delete(`${API}/contratos/${contractId}`);
        toast.success(response.data.message);
        await loadContracts();
        await loadContractStats();
      } catch (error) {
        console.error('Erro ao excluir contrato:', error);
        toast.error(error.response?.data?.detail || 'Erro ao excluir contrato');
      }
    }
  };

  const openContractModal = (contract = null) => {
    setEditingContract(contract);
    setShowContractModal(true);
  };

  const closeContractModal = () => {
    setShowContractModal(false);
    setEditingContract(null);
  };

  // 🐾 Pet Shop Product functions
  const handleCreateProduct = async (productData) => {
    try {
      console.log('Creating product:', productData);
      const response = await axios.post(`${API}/petshop/products`, productData);
      
      toast.success('Produto criado com sucesso!');
      setShowProductModal(false);
      setEditingProduct(null);
      
      // Recarregar dados do Pet Shop se estivermos na view
      if (activeView === 'petshop') {
        // Trigger reload - será implementado quando o PetShopView estiver funcional
        window.location.reload();
      }
    } catch (error) {
      console.error('Erro ao criar produto:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar produto');
    }
  };

  const handleUpdateProduct = async (productId, productData) => {
    try {
      console.log('Updating product:', productId, productData);
      const response = await axios.put(`${API}/petshop/products/${productId}`, productData);
      
      toast.success('Produto atualizado com sucesso!');
      setShowProductModal(false);
      setEditingProduct(null);
      
      // Recarregar dados do Pet Shop se estivermos na view
      if (activeView === 'petshop') {
        window.location.reload();
      }
    } catch (error) {
      console.error('Erro ao atualizar produto:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar produto');
    }
  };

  // ✨ Biblical Messages Functions
  const getDailyMessage = () => {
    const today = new Date();
    const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / 1000 / 60 / 60 / 24);
    
    // Alternate between biblical and motivational messages
    const useBiblical = dayOfYear % 2 === 0;
    const messages = useBiblical ? biblicalMessages : motivationalMessages;
    
    // Use day of year to get consistent daily message
    const messageIndex = dayOfYear % messages.length;
    const selectedMessage = messages[messageIndex];
    
    return {
      ...selectedMessage,
      type: useBiblical ? 'biblical' : 'motivational',
      date: today.toDateString()
    };
  };

  // Load daily message on component mount and user login
  React.useEffect(() => {
    if (user) {
      const message = getDailyMessage();
      setDailyMessage(message);
    }
  }, [user]);

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
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar Desktop */}
      <div className={`hidden lg:flex lg:flex-col bg-white shadow-lg transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}>
        <SidebarComponent 
          collapsed={sidebarCollapsed}
          onToggle={() => {
            setSidebarCollapsed(!sidebarCollapsed);
            localStorage.setItem('sidebarCollapsed', JSON.stringify(!sidebarCollapsed));
          }}
          activeView={activeView}
          onViewChange={setActiveView}
          onCreditCardsClick={() => {
            setActiveView('credit-cards');
            loadCreditCardInvoices();
          }}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar com Search */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-4 py-3 lg:px-6">
          <div className="flex items-center justify-between">
            {/* Mobile Menu Button + Logo */}
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setShowMobileMenu(!showMobileMenu)}
                className="lg:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="text-xl font-bold text-gray-900 lg:hidden">OrçaZen</h1>
            </div>

            {/* Global Search Bar */}
            <GlobalSearchBar 
              isVisible={showSearchBar}
              onToggle={() => setShowSearchBar(!showSearchBar)}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              searchResults={searchResults}
            />

            {/* User Info & Notifications */}
            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center space-x-3">
                <span className="text-gray-600 text-sm">Bem-vindo,</span>
                <span className="font-medium text-gray-900">
                  {user?.name || user?.email?.split('@')[0] || 'Usuário'}
                </span>
              </div>

              {/* Notifications */}
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
                className="text-gray-600 hover:text-gray-900 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Sair"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </header>

        {/* Mobile Navigation Menu */}
        {showMobileMenu && (
          <div className="lg:hidden bg-white shadow-lg border-t border-gray-200 absolute w-full z-40">
            <div className="px-4 py-2 space-y-1">
              <button
                onClick={() => {setActiveView('dashboard'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'dashboard' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => {setActiveView('transactions'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'transactions' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                💳 Transações
              </button>
              <button
                onClick={() => {setActiveView('accounts'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'accounts' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🏦 Contas
              </button>
              <button
                onClick={() => {setActiveView('goals'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'goals' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🎯 Metas
              </button>
              <button
                onClick={() => {setActiveView('budgets'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'budgets' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                📈 Orçamentos
              </button>
              <button
                onClick={() => {setActiveView('ai'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'ai' ? 'bg-purple-100 text-purple-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🧠 IA Financeira
              </button>
              <button
                onClick={() => {setActiveView('consortiums'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'consortiums' ? 'bg-green-100 text-green-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🏠 Consórcios
              </button>
              <button
                onClick={() => {setActiveView('credit-cards'); loadCreditCardInvoices(); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'credit-cards' ? 'bg-orange-100 text-orange-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                💳 Cartões
              </button>
              <button
                onClick={() => {setActiveView('profile'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'profile' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                👤 Perfil
              </button>
              <button
                onClick={() => {setActiveView('import'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'import' ? 'bg-green-100 text-green-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                📄 Importar
              </button>
              <button
                onClick={() => {setActiveView('contracts'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'contracts' ? 'bg-purple-100 text-purple-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🏠 Contratos
              </button>
              <button
                onClick={() => {setActiveView('petshop'); setShowMobileMenu(false);}}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all ${
                  activeView === 'petshop' ? 'bg-pink-100 text-pink-700' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🐾 Pet Shop
              </button>
            </div>
          </div>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <div className="p-4 lg:p-8">{/* Content will be here */}
        {activeView === 'dashboard' && (
          <>
            {/* ✨ Daily Inspirational Message */}
            {dailyMessage && (
              <div className="mb-8">
                <div className={`rounded-2xl p-6 shadow-lg border-l-4 ${
                  dailyMessage.type === 'biblical' 
                    ? 'bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-500' 
                    : 'bg-gradient-to-r from-green-50 to-blue-50 border-green-500'
                }`}>
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-full ${
                      dailyMessage.type === 'biblical' 
                        ? 'bg-indigo-100 text-indigo-600' 
                        : 'bg-green-100 text-green-600'
                    }`}>
                      {dailyMessage.type === 'biblical' ? '📖' : '💡'}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className={`font-semibold ${
                          dailyMessage.type === 'biblical' 
                            ? 'text-indigo-900' 
                            : 'text-green-900'
                        }`}>
                          {dailyMessage.type === 'biblical' ? 'Palavra do Dia' : 'Inspiração do Dia'}
                        </h3>
                        <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded-full">
                          {new Date().toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                      <p className={`text-sm leading-relaxed mb-2 ${
                        dailyMessage.type === 'biblical' 
                          ? 'text-indigo-800' 
                          : 'text-green-800'
                      }`}>
                        "{dailyMessage.message}"
                      </p>
                      {dailyMessage.verse && (
                        <p className="text-xs font-medium text-indigo-600">
                          — {dailyMessage.verse}
                        </p>
                      )}
                      <div className="mt-3">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          dailyMessage.type === 'biblical' 
                            ? 'bg-indigo-100 text-indigo-700' 
                            : 'bg-green-100 text-green-700'
                        }`}>
                          #{dailyMessage.category}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Enhanced Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* SALDO TOTAL CONSOLIDADO - GRANDE DESTAQUE */}
          <div className="md:col-span-2 lg:col-span-2 bg-gradient-to-br from-blue-600 to-purple-700 rounded-2xl p-8 text-white shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium opacity-90">Saldo Total Consolidado</h3>
                <p className="text-4xl font-bold">{formatCurrency(summary?.total_balance || 0)}</p>
              </div>
              <div className="p-3 bg-white bg-opacity-20 rounded-full">
                <DollarSign size={32} />
              </div>
            </div>
            <div className="text-sm opacity-75">
              Soma de todas as contas ativas • Atualizado em tempo real
            </div>
            <div className="mt-4 flex items-center text-sm">
              {(summary?.total_balance || 0) >= 0 ? (
                <>
                  <TrendingUp className="w-4 h-4 mr-1 text-green-300" />
                  <span className="text-green-300">Saldo Positivo</span>
                </>
              ) : (
                <>
                  <TrendingDown className="w-4 h-4 mr-1 text-red-300" />
                  <span className="text-red-300">Atenção: Saldo Negativo</span>
                </>
              )}
            </div>
          </div>

          {/* PROGRESSO DAS METAS FINANCEIRAS - ENHANCED */}
          <div className="md:col-span-2 lg:col-span-2 bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-800">🎯 Progresso das Metas Financeiras</h3>
              <Target className="text-blue-600" size={24} />
            </div>
            
            <div className="space-y-6">
              {/* Active Goals Summary */}
              {goalsStats && (
                <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{goalsStats.active_goals || 0}</p>
                    <p className="text-xs text-gray-600">Metas Ativas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{goalsStats.achieved_goals || 0}</p>
                    <p className="text-xs text-gray-600">Conquistadas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">
                      {goalsStats.overall_progress ? `${goalsStats.overall_progress.toFixed(1)}%` : '0%'}
                    </p>
                    <p className="text-xs text-gray-600">Progresso Geral</p>
                  </div>
                </div>
              )}

              {/* Individual Goals Progress */}
              {goals && goals.length > 0 ? (
                <div className="space-y-4 max-h-64 overflow-y-auto">
                  {goals.slice(0, 4).map((goal) => {
                    const progress = goal.target_amount > 0 ? (goal.current_amount / goal.target_amount) * 100 : 0;
                    const isCompleted = progress >= 100;
                    
                    return (
                      <div key={goal.id} className="space-y-3">
                        <div className="flex justify-between items-center">
                          <div>
                            <h4 className="font-medium text-gray-900 flex items-center gap-2">
                              <span className={`text-sm px-2 py-1 rounded ${
                                goal.priority === 'Alta' ? 'bg-red-100 text-red-700' :
                                goal.priority === 'Média' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {goal.priority}
                              </span>
                              {goal.name}
                              {isCompleted && <span className="text-green-600">✅</span>}
                            </h4>
                            <p className="text-sm text-gray-500">{goal.category}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-gray-900">
                              {formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}
                            </p>
                            <p className="text-xs text-gray-500">
                              Faltam: {formatCurrency(Math.max(0, goal.target_amount - goal.current_amount))}
                            </p>
                          </div>
                        </div>
                        
                        {/* Enhanced Progress Bar */}
                        <div className="relative">
                          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 relative ${
                                isCompleted 
                                  ? 'bg-gradient-to-r from-green-400 to-green-600' 
                                  : progress > 75 
                                    ? 'bg-gradient-to-r from-blue-400 to-blue-600'
                                    : progress > 50
                                      ? 'bg-gradient-to-r from-yellow-400 to-orange-500'
                                      : 'bg-gradient-to-r from-gray-400 to-gray-500'
                              } ${progress > 0 ? 'animate-pulse' : ''}`}
                              style={{ 
                                width: `${Math.min(progress, 100)}%`,
                                boxShadow: progress > 0 ? 'inset 0 1px 2px rgba(0,0,0,0.1)' : 'none'
                              }}
                            >
                              {progress > 0 && (
                                <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent"></div>
                              )}
                            </div>
                          </div>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xs font-bold text-white drop-shadow-lg">
                              {progress.toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        {/* Goal Timeline */}
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>
                            {goal.auto_contribution && `+${formatCurrency(goal.auto_contribution)}/mês`}
                          </span>
                          <span>
                            Meta: {formatDate(goal.target_date)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                  
                  {goals.length > 4 && (
                    <button
                      onClick={() => setActiveView('goals')}
                      className="w-full py-2 text-center text-blue-600 hover:text-blue-800 text-sm font-medium border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                    >
                      Ver todas as {goals.length} metas →
                    </button>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Target className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <h4 className="font-medium text-gray-700 mb-2">Nenhuma meta definida</h4>
                  <p className="text-sm text-gray-500 mb-4">
                    Crie suas metas financeiras para acompanhar seu progresso
                  </p>
                  <button
                    onClick={() => {
                      setActiveView('goals');
                      setShowGoalModal(true);
                    }}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
                  >
                    + Criar Meta
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Cards de Resumo Mensal Aprimorados */}
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

            {/* Enhanced Charts Section with Drill-down */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Enhanced Expense Chart with Drill-down */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">📊 Despesas por Categoria</h3>
                  <button
                    onClick={() => {
                      setReportType('expenses-by-category');
                      setShowReportsModal(true);
                    }}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Ver Detalhes →
                  </button>
                </div>
                {expenseChartData.length > 0 ? (
                  <div className="space-y-4">
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
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                    
                    {/* Category Breakdown */}
                    <div className="max-h-32 overflow-y-auto space-y-2">
                      {expenseChartData
                        .sort((a, b) => b.value - a.value)
                        .slice(0, 5)
                        .map((category, index) => {
                          const percentage = ((category.value / expenseChartData.reduce((sum, cat) => sum + cat.value, 0)) * 100).toFixed(1);
                          return (
                            <div key={index} className="flex items-center justify-between py-1">
                              <div className="flex items-center space-x-2">
                                <div 
                                  className="w-3 h-3 rounded-full"
                                  style={{ backgroundColor: category.color }}
                                ></div>
                                <span className="text-sm text-gray-700">{category.name}</span>
                              </div>
                              <div className="text-right">
                                <span className="text-sm font-medium text-gray-900">
                                  {formatCurrency(category.value)}
                                </span>
                                <span className="text-xs text-gray-500 ml-2">({percentage}%)</span>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <PieChart className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <p>Nenhuma despesa encontrada neste mês</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Enhanced Income Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">💰 Receitas por Categoria</h3>
                  <button
                    onClick={() => {
                      setReportType('income-by-category');
                      setShowReportsModal(true);
                    }}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Ver Detalhes →
                  </button>
                </div>
                {incomeChartData.length > 0 ? (
                  <div className="space-y-4">
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
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                    
                    {/* Income Breakdown */}
                    <div className="max-h-32 overflow-y-auto space-y-2">
                      {incomeChartData
                        .sort((a, b) => b.value - a.value)
                        .map((category, index) => {
                          const percentage = ((category.value / incomeChartData.reduce((sum, cat) => sum + cat.value, 0)) * 100).toFixed(1);
                          return (
                            <div key={index} className="flex items-center justify-between py-1">
                              <div className="flex items-center space-x-2">
                                <div 
                                  className="w-3 h-3 rounded-full"
                                  style={{ backgroundColor: category.color }}
                                ></div>
                                <span className="text-sm text-gray-700">{category.name}</span>
                              </div>
                              <div className="text-right">
                                <span className="text-sm font-medium text-gray-900">
                                  {formatCurrency(category.value)}
                                </span>
                                <span className="text-xs text-gray-500 ml-2">({percentage}%)</span>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <PieChart className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <p>Nenhuma receita encontrada neste mês</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Advanced Charts Section with Drill-down */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Enhanced Balance Evolution Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">📈 Evolução do Saldo (12 meses)</h3>
                  <button
                    onClick={() => {
                      setReportType('detailed-cash-flow');
                      setShowReportsModal(true);
                    }}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Relatório Completo →
                  </button>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={generateBalanceEvolutionData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="month" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                    />
                    <YAxis 
                      tickFormatter={(value) => formatCurrency(value)}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                    />
                    <Tooltip 
                      formatter={(value) => [formatCurrency(value), 'Saldo']}
                      contentStyle={{
                        backgroundColor: '#f9fafb',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="balance" 
                      stroke="#3B82F6" 
                      strokeWidth={3}
                      dot={{ r: 6, fill: '#3B82F6', strokeWidth: 2, stroke: '#ffffff' }}
                      activeDot={{ r: 8, fill: '#1D4ED8' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
                
                {/* Balance Trend Indicator */}
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Tendência dos últimos 3 meses</span>
                    <div className="flex items-center">
                      <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                      <span className="text-green-600 font-medium">Em crescimento</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Enhanced Income vs Expenses Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">⚖️ Receitas vs Despesas (12 meses)</h3>
                  <div className="flex space-x-2">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-1"></div>
                      <span className="text-xs text-gray-600">Receitas</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-red-500 rounded-full mr-1"></div>
                      <span className="text-xs text-gray-600">Despesas</span>
                    </div>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={generateIncomeVsExpensesData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="month" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                    />
                    <YAxis 
                      tickFormatter={(value) => formatCurrency(value)}
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [formatCurrency(value), name]}
                      contentStyle={{
                        backgroundColor: '#f9fafb',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                      }}
                    />
                    <Bar dataKey="income" fill="#10B981" name="Receitas" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="expenses" fill="#EF4444" name="Despesas" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                
                {/* Monthly Balance Indicator */}
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-xs text-green-600 font-medium">Receita Média</p>
                    <p className="text-lg font-bold text-green-700">
                      {formatCurrency(summary?.monthly_income || 0)}
                    </p>
                  </div>
                  <div className="p-3 bg-red-50 rounded-lg">
                    <p className="text-xs text-red-600 font-medium">Despesa Média</p>
                    <p className="text-lg font-bold text-red-700">
                      {formatCurrency(summary?.monthly_expenses || 0)}
                    </p>
                  </div>
                </div>
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

        {/* 🧠 AI VIEW */}
        {activeView === 'ai' && (
          <AIView
            insights={aiInsights}
            onRefreshInsights={loadAIInsights}
            onOpenChat={() => setShowAIChat(true)}
            onOpenInsights={() => setShowAIInsights(true)}
          />
        )}

        {/* 🏠 CONSORTIUM VIEW */}
        {activeView === 'consortiums' && (
          <ConsortiumView
            consortiums={consortiums}
            onRefresh={loadDashboard}
            onCreateNew={() => setShowConsortiumModal(true)}
            onViewDetails={loadConsortiumSummary}
          />
        )}

        {/* 💳 CREDIT CARD VIEW */}
        {activeView === 'credit-cards' && (
          <CreditCardView
            invoices={creditCardInvoices}
            loading={loadingInvoices}
            onRefresh={loadCreditCardInvoices}
            onGenerate={generateCreditCardInvoices}
            onPay={payCreditCardInvoice}
          />
        )}

        {/* 👤 USER PROFILE VIEW */}
        {activeView === 'profile' && (
          <ProfileView
            user={user}
            onRefresh={loadDashboard}
            onEditProfile={openProfileModal}
            onChangePassword={openPasswordModal}
          />
        )}

        {/* 📄 FILE IMPORT VIEW */}
        {activeView === 'import' && (
          <FileImportView
            importStep={importStep}
            selectedFiles={selectedFiles}
            importPreview={importPreview}
            selectedTransactions={selectedTransactions}
            importLoading={importLoading}
            onFileUpload={handleFileUpload}
            onImportConfirm={handleImportConfirm}
            onTransactionToggle={toggleTransactionSelection}
            onReset={resetImport}
          />
        )}

        {/* 🏠 CONTRACTS VIEW */}
        {activeView === 'contracts' && (
          <ContractsView
            contracts={contracts}
            contractStats={contractStats}
            contractFilters={contractFilters}
            contractsLoading={contractsLoading}
            onLoadContracts={loadContracts}
            onLoadStats={loadContractStats}
            onFiltersChange={setContractFilters}
            onCreateContract={openContractModal}
            onEditContract={openContractModal}
            onDeleteContract={handleDeleteContract}
          />
        )}

        {/* 🐾 PET SHOP VIEW */}
        {activeView === 'petshop' && (
          <PetShopView />
        )}
      </div>

      {/* Fixed Quick Actions - Show when scrolled on dashboard */}
      {showFixedActions && (
        <div className="fixed bottom-6 right-6 z-40">
          <div className="bg-white rounded-xl shadow-2xl border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">Ações Rápidas</h3>
            <div className="grid grid-cols-2 gap-3">
              {/* Add Income */}
              <button
                onClick={openIncomeModal}
                className="flex flex-col items-center justify-center p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors group"
                title="Adicionar Receita"
              >
                <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center mb-2 group-hover:bg-green-600 transition-colors">
                  <Plus className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-green-700">Receita</span>
              </button>

              {/* Add Expense */}
              <button
                onClick={openExpenseModal}
                className="flex flex-col items-center justify-center p-3 bg-red-50 hover:bg-red-100 rounded-lg transition-colors group"
                title="Adicionar Despesa"
              >
                <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center mb-2 group-hover:bg-red-600 transition-colors">
                  <Plus className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-red-700">Despesa</span>
              </button>

              {/* Transfer */}
              <button
                onClick={openTransferModal}
                className="flex flex-col items-center justify-center p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors group"
                title="Transferir entre Contas"
              >
                <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center mb-2 group-hover:bg-blue-600 transition-colors">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-blue-700">Transferir</span>
              </button>

              {/* Reports */}
              <button
                onClick={openReportsModal}
                className="flex flex-col items-center justify-center p-3 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors group"
                title="Ver Relatórios"
              >
                <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center mb-2 group-hover:bg-purple-600 transition-colors">
                  <FileText className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs font-medium text-purple-700">Relatórios</span>
              </button>
            </div>
            
            {/* Hide button */}
            <div className="mt-3 pt-3 border-t border-gray-200">
              <button
                onClick={() => setShowFixedActions(false)}
                className="w-full text-xs text-gray-500 hover:text-gray-700 transition-colors"
                title="Ocultar ações rápidas"
              >
                ✕ Ocultar
              </button>
            </div>
          </div>
        </div>
      )}

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

      {/* 🧠 IA Modals */}
      {showAIChat && (
        <AIChatModal
          messages={chatMessages}
          onClose={() => setShowAIChat(false)}
          onSendMessage={sendChatMessage}
        />
      )}

      {showAIInsights && (
        <AIInsightsModal
          insights={aiInsights}
          onClose={() => setShowAIInsights(false)}
          onRefresh={loadAIInsights}
        />
      )}

      {/* 🏠 Consortium Modals */}
      {showConsortiumModal && (
        <ConsortiumModal
          onClose={() => {
            setShowConsortiumModal(false);
            setEditingItem(null);
          }}
          onCreate={handleCreateConsortium}
        />
      )}

      {showConsortiumDetails && (
        <ConsortiumDetailsModal
          consortium={selectedConsortium}
          onClose={() => {
            setShowConsortiumDetails(false);
            setSelectedConsortium(null);
          }}
          onPayment={handleConsortiumPayment}
          onMarkContemplation={handleMarkContemplation}
        />
      )}

      {/* 👤 User Profile Modals */}
      {showProfileModal && (
        <ProfileModal
          profileData={profileData}
          onClose={() => setShowProfileModal(false)}
          onUpdate={handleUpdateProfile}
          onProfileDataChange={setProfileData}
        />
      )}

      {showPasswordModal && (
        <PasswordModal
          passwordData={passwordData}
          onClose={() => setShowPasswordModal(false)}
          onChange={handleChangePassword}
          onPasswordDataChange={setPasswordData}
        />
      )}

      {/* 🏠 Contract Modal */}
      {showContractModal && (
        <ContractModal
          contract={editingContract}
          onClose={closeContractModal}
          onCreate={handleCreateContract}
          onUpdate={handleUpdateContract}
        />
      )}

      {/* 🐾 Pet Shop Product Modal */}
      {showProductModal && (
        <PetShopProductModal
          product={editingProduct}
          onClose={() => {
            setShowProductModal(false);
            setEditingProduct(null);
          }}
          onCreate={handleCreateProduct}
          onUpdate={handleUpdateProduct}
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

        {/* Advanced Filters COMPLETOS conforme solicitação */}
        <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-4">
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

          {/* NOVO FILTRO: Tipo de Despesa */}
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.expense_type || ''}
            onChange={(e) => setFilters({...filters, expense_type: e.target.value})}
          >
            <option value="">Todos os tipos de despesa</option>
            <option value="Fixo">Fixo</option>
            <option value="Variável">Variável</option>
            <option value="Parcelado">Parcelado</option>
          </select>

          {/* NOVO FILTRO: Status Pago/Pendente */}
          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            value={filters.status}
            onChange={(e) => setFilters({...filters, status: e.target.value})}
          >
            <option value="">Todos os status</option>
            <option value="Pago">Pago</option>
            <option value="Pendente">Pendente</option>
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {goals.map((goal) => {
                const progress = getGoalProgress(goal);
                const daysRemaining = getDaysRemaining(goal.target_date);
                
                return (
                  <div key={goal.id} className="border rounded-xl p-6 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900">{goal.name}</h3>
                        <p className="text-sm text-gray-500">{goal.category}</p>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-2 ${getPriorityColor(goal.priority)}`}>
                          {goal.priority}
                        </span>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => onContribute(goal)}
                          className="text-green-600 hover:text-green-800"
                          title="Contribuir para meta"
                        >
                          <Plus size={16} />
                        </button>
                        <button
                          onClick={() => onEdit(goal)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Editar meta"
                        >
                          <SquarePen size={16} />
                        </button>
                        <button
                          onClick={() => onDelete(goal.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Excluir meta"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    {goal.description && (
                      <p className="text-sm text-gray-600 mb-4">{goal.description}</p>
                    )}

                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Meta:</span>
                        <span className="font-medium">{formatCurrency(goal.target_amount)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Poupado:</span>
                        <span className="font-medium text-green-600">{formatCurrency(goal.current_amount)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Restante:</span>
                        <span className="font-medium">{formatCurrency(goal.target_amount - goal.current_amount)}</span>
                      </div>
                      
                      <div className="mt-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm text-gray-600">Progresso</span>
                          <span className="text-sm font-medium">{progress.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                            style={{width: `${Math.min(progress, 100)}%`}}
                          />
                        </div>
                      </div>

                      <div className="flex justify-between text-sm pt-2 border-t">
                        <span className="text-gray-600">Data limite:</span>
                        <div className="text-right">
                          <span className="font-medium">{formatDate(goal.target_date)}</span>
                          <div className={`text-xs ${daysRemaining > 30 ? 'text-green-600' : daysRemaining > 0 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {daysRemaining > 0 ? `${daysRemaining} dias restantes` : 'Meta vencida'}
                          </div>
                        </div>
                      </div>

                      {goal.is_achieved && (
                        <div className="flex items-center justify-center mt-4 p-3 bg-green-100 rounded-lg">
                          <Target className="w-5 h-5 text-green-600 mr-2" />
                          <span className="text-green-800 font-medium">Meta atingida!</span>
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
            <BrazilianCurrencyInput
              value={formData.initial_balance}
              onChange={(value) => setFormData({...formData, initial_balance: value})}
              placeholder="R$ 0,00"
              required
            />
          </div>

          {formData.type === 'Cartão de Crédito' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Limite de Crédito</label>
                <BrazilianCurrencyInput
                  value={formData.credit_limit}
                  onChange={(value) => setFormData({...formData, credit_limit: value})}
                  placeholder="R$ 0,00"
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
    expense_type: transaction?.expense_type || 'Variável', // NOVO CAMPO
    due_date: transaction?.due_date ? formatDateForInput(transaction.due_date) : '', // NOVO CAMPO
    paid_by: transaction?.paid_by || '', // NOVO CAMPO
    installment_number: transaction?.installment_number || '', // NOVO CAMPO
    total_installments: transaction?.total_installments || '', // NOVO CAMPO
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
        value: parseFloat(formData.value),
        expense_type: formData.expense_type || 'Variável',
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        paid_by: formData.paid_by || null,
        installment_number: formData.installment_number || null,
        total_installments: formData.total_installments || null
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
              <BrazilianCurrencyInput
                value={formData.value}
                onChange={(value) => setFormData({...formData, value: value})}
                placeholder="R$ 0,00"
                required
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
              <HierarchicalCategorySelect
                value={formData.category_id}
                onChange={(categoryId) => setFormData({...formData, category_id: categoryId})}
                categories={categories}
                type={type}
                placeholder="Selecione uma categoria"
              />
            </div>
          </div>

          {/* Status, Tipo de Despesa e Data de Vencimento */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

            {type === 'Despesa' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de Despesa</label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  value={formData.expense_type}
                  onChange={(e) => setFormData({...formData, expense_type: e.target.value})}
                >
                  <option value="Fixo">Fixo</option>
                  <option value="Variável">Variável</option>
                  <option value="Parcelado">Parcelado</option>
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Data de Vencimento</label>
              <input
                type="date"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.due_date}
                onChange={(e) => setFormData({...formData, due_date: e.target.value})}
              />
            </div>
          </div>

          {/* Parcelamento (se Parcelado) e Pago Por */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {formData.expense_type === 'Parcelado' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Parcela Atual</label>
                  <input
                    type="number"
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                    value={formData.installment_number}
                    onChange={(e) => setFormData({...formData, installment_number: e.target.value})}
                    placeholder="Ex: 3"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Total de Parcelas</label>
                  <input
                    type="number"
                    min="2"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                    value={formData.total_installments}
                    onChange={(e) => setFormData({...formData, total_installments: e.target.value})}
                    placeholder="Ex: 12"
                  />
                </div>
              </>
            )}
            
            {(!formData.expense_type || formData.expense_type !== 'Parcelado') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Pago Por</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  value={formData.paid_by}
                  onChange={(e) => setFormData({...formData, paid_by: e.target.value})}
                  placeholder="Nome da pessoa que pagou"
                />
              </div>
            )}
          </div>

          {/* Observações/Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Observações/Tags</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={formData.observation}
              onChange={(e) => setFormData({...formData, observation: e.target.value})}
              placeholder="Ex: #viagem, nota fiscal, etc."
            />
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
            <BrazilianCurrencyInput
              value={formData.value}
              onChange={(value) => setFormData({...formData, value: value})}
              placeholder="R$ 0,00"
              required
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

// Enhanced Reports Modal Component with New Features
const ReportsModal = ({ summary, transactions, accounts, onClose }) => {
  const [reportType, setReportType] = useState('overview');
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [selectedAccount, setSelectedAccount] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch enhanced report data
  const fetchReportData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      let url = '';
      let params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end
      });

      if (selectedAccount) params.append('account_id', selectedAccount);
      if (selectedCategory) params.append('category_id', selectedCategory);

      switch (reportType) {
        case 'expenses-by-category':
          url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/expenses-by-category?${params}`;
          break;
        case 'income-by-category':
          url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/income-by-category?${params}`;
          break;
        case 'detailed-cash-flow':
          url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/detailed-cash-flow?${params}`;
          break;
        case 'by-tags':
          url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/by-tags?${params}`;
          break;
        default:
          setLoading(false);
          return;
      }

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setReportData(data);
      }
    } catch (error) {
      console.error('Error fetching report data:', error);
      toast.error('Erro ao carregar dados do relatório');
    }
    setLoading(false);
  };

  // Export enhanced CSV with more data
  const exportEnhancedCSV = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        report_type: reportType === 'overview' ? 'transactions' : reportType.replace('-', '-'),
        start_date: dateRange.start,
        end_date: dateRange.end
      });

      if (selectedAccount) params.append('account_id', selectedAccount);
      if (selectedCategory) params.append('category_id', selectedCategory);

      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/reports/export-excel?${params}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Create and download file
        const blob = new Blob([data.csv_content], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', data.filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        toast.success(`Relatório exportado: ${data.total_records} registros`);
      } else {
        toast.error('Erro ao exportar relatório');
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      toast.error('Erro ao exportar relatório');
    }
  };

  // Load report data when type or filters change
  useEffect(() => {
    if (reportType !== 'overview') {
      fetchReportData();
    }
  }, [reportType, dateRange, selectedAccount, selectedCategory]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-7xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-semibold text-gray-900">📊 Relatórios Financeiros Avançados</h3>
          <div className="flex items-center gap-3">
            <button
              onClick={exportEnhancedCSV}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              <Download size={16} />
              Exportar Excel
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl p-1"
            >
              ×
            </button>
          </div>
        </div>

        {/* Enhanced Report Controls */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Relatório</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 w-full"
            >
              <option value="overview">Visão Geral</option>
              <option value="detailed-cash-flow">Fluxo de Caixa Detalhado</option>
              <option value="expenses-by-category">Despesas por Categoria</option>
              <option value="income-by-category">Receitas por Categoria</option>
              <option value="by-tags">Relatório por Tags</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Inicial</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data Final</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filtrar por Conta</label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 w-full"
            >
              <option value="">Todas as contas</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>{account.name}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={fetchReportData}
              disabled={loading}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Carregando...' : 'Atualizar'}
            </button>
          </div>
        </div>

        {/* Report Content */}
        <div className="space-y-8">
          {reportType === 'overview' && (
            <>
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
            </>
          )}

          {/* Enhanced Report Views */}
          {reportType !== 'overview' && reportData && (
            <EnhancedReportView reportType={reportType} data={reportData} />
          )}

          {reportType !== 'overview' && loading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Carregando relatório...</p>
            </div>
          )}
        </div>

        <div className="flex justify-end mt-8">
          <button
            onClick={onClose}
            className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced Report View Component
const EnhancedReportView = ({ reportType, data }) => {
  if (reportType === 'expenses-by-category' && data.category_data) {
    return (
      <div>
        <h4 className="text-lg font-semibold mb-4">
          Despesas por Categoria - Total: {formatCurrency(data.total_expenses)}
        </h4>
        <div className="space-y-4">
          {Object.entries(data.category_data).map(([categoryName, categoryData]) => (
            <div key={categoryName} className="border rounded-lg p-4">
              <div className="flex justify-between items-center mb-3">
                <h5 className="font-medium text-gray-900">{categoryName}</h5>
                <div className="text-right">
                  <p className="font-bold text-red-600">{formatCurrency(categoryData.total)}</p>
                  <p className="text-sm text-gray-500">{categoryData.percentage.toFixed(1)}% do total</p>
                </div>
              </div>
              
              {/* Subcategories */}
              {categoryData.subcategories && Object.keys(categoryData.subcategories).length > 0 && (
                <div className="mt-3 pl-4 border-l-2 border-gray-200">
                  <h6 className="text-sm font-medium text-gray-700 mb-2">Subcategorias:</h6>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {Object.entries(categoryData.subcategories).map(([subName, subData]) => (
                      <div key={subName} className="bg-gray-50 rounded p-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">{subName}</span>
                          <div className="text-right">
                            <p className="font-medium text-red-600">{formatCurrency(subData.total)}</p>
                            <p className="text-xs text-gray-500">{subData.count} transações</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (reportType === 'income-by-category' && data.category_data) {
    return (
      <div>
        <h4 className="text-lg font-semibold mb-4">
          Receitas por Categoria - Total: {formatCurrency(data.total_income)}
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(data.category_data).map(([categoryName, categoryData]) => (
            <div key={categoryName} className="border rounded-lg p-4">
              <div className="flex justify-between items-center">
                <h5 className="font-medium text-gray-900">{categoryName}</h5>
                <div className="text-right">
                  <p className="font-bold text-green-600">{formatCurrency(categoryData.total)}</p>
                  <p className="text-sm text-gray-500">
                    {categoryData.percentage.toFixed(1)}% • {categoryData.count} transações
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (reportType === 'detailed-cash-flow' && data.monthly_data) {
    return (
      <div>
        <h4 className="text-lg font-semibold mb-4">Fluxo de Caixa Detalhado</h4>
        
        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-green-50 p-4 rounded-lg">
            <h5 className="font-medium text-green-800 mb-1">Total de Receitas</h5>
            <p className="text-2xl font-bold text-green-900">
              {formatCurrency(data.summary.total_income)}
            </p>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <h5 className="font-medium text-red-800 mb-1">Total de Despesas</h5>
            <p className="text-2xl font-bold text-red-900">
              {formatCurrency(data.summary.total_expenses)}
            </p>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h5 className="font-medium text-blue-800 mb-1">Fluxo Líquido</h5>
            <p className={`text-2xl font-bold ${
              data.summary.net_flow >= 0 ? 'text-green-900' : 'text-red-900'
            }`}>
              {formatCurrency(data.summary.net_flow)}
            </p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h5 className="font-medium text-purple-800 mb-1">Período</h5>
            <p className="text-sm text-purple-900 font-medium">
              {formatDate(data.summary.period.start)} até<br/>
              {formatDate(data.summary.period.end)}
            </p>
          </div>
        </div>

        {/* Monthly Breakdown */}
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mês</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Receitas</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Despesas</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Saldo Líquido</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {Object.entries(data.monthly_data)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([month, monthData]) => (
                <tr key={month} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">
                    {new Date(month + '-01').toLocaleDateString('pt-BR', { 
                      month: 'long', 
                      year: 'numeric' 
                    })}
                  </td>
                  <td className="px-6 py-4 text-right font-bold text-green-600">
                    {formatCurrency(monthData.income)}
                  </td>
                  <td className="px-6 py-4 text-right font-bold text-red-600">
                    {formatCurrency(monthData.expenses)}
                  </td>
                  <td className={`px-6 py-4 text-right font-bold ${
                    monthData.net >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(monthData.net)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (reportType === 'by-tags' && data.tag_data) {
    return (
      <div>
        <h4 className="text-lg font-semibold mb-4">Relatório por Tags</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(data.tag_data).map(([tagName, tagData]) => (
            <div key={tagName} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div 
                    className="w-4 h-4 rounded-full mr-3"
                    style={{ backgroundColor: tagData.color }}
                  ></div>
                  <h5 className="font-medium text-gray-900">{tagName}</h5>
                </div>
                <span className="text-sm bg-gray-100 px-2 py-1 rounded">
                  {tagData.count} transações
                </span>
              </div>
              
              <div className="space-y-2">
                {tagData.total_income > 0 && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Receitas:</span>
                    <span className="font-medium text-green-600">
                      {formatCurrency(tagData.total_income)}
                    </span>
                  </div>
                )}
                
                {tagData.total_expenses > 0 && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Despesas:</span>
                    <span className="font-medium text-red-600">
                      {formatCurrency(tagData.total_expenses)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="text-center py-8">
      <p className="text-gray-500">Nenhum dado disponível para este relatório</p>
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

  const goalCategories = ['Emergência', 'Casa Própria', 'Viagem', 'Aposentadoria', 'Lazer', 'Outros'];
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

// ============================================================================
// 📊 COMPONENTE DE DROPDOWN HIERÁRQUICO DE CATEGORIAS
// ============================================================================

const HierarchicalCategorySelect = ({ value, onChange, categories, type, placeholder = "Selecione uma categoria" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  
  useEffect(() => {
    if (value && categories.length > 0) {
      // Find selected category by ID in flat structure
      const selected = categories.find(cat => cat.id === value);
      if (selected) {
        setSelectedCategory(selected);
      }
    }
  }, [value, categories]);

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    onChange(category.id);
    setIsOpen(false);
  };

  // Transform flat structure to hierarchical structure
  const buildHierarchicalCategories = (flatCategories) => {
    const typeFiltered = flatCategories.filter(cat => cat.type === type);
    const parentCategories = typeFiltered.filter(cat => !cat.parent_category_id);
    
    return parentCategories.map(parent => ({
      ...parent,
      subcategories: typeFiltered.filter(cat => cat.parent_category_id === parent.id)
    }));
  };

  const hierarchicalCategories = buildHierarchicalCategories(categories);

  return (
    <div className="relative">
      {/* Selected Category Display */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all bg-white text-left flex items-center justify-between"
      >
        <div className="flex items-center">
          {selectedCategory ? (
            <>
              <span className="text-lg mr-2">{selectedCategory.icon}</span>
              <div>
                <span className="font-medium">{selectedCategory.name}</span>
                {selectedCategory.parent_category_name && (
                  <span className="text-sm text-gray-500 ml-2">
                    ({selectedCategory.parent_category_name})
                  </span>
                )}
              </div>
            </>
          ) : (
            <span className="text-gray-500">{placeholder}</span>
          )}
        </div>
        <div className="text-gray-400">
          {isOpen ? '▲' : '▼'}
        </div>
      </button>

      {/* Dropdown Options */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {hierarchicalCategories.map((mainCategory) => (
            <div key={mainCategory.id}>
              {/* Main Category */}
              <button
                type="button"
                onClick={() => handleCategorySelect(mainCategory)}
                className="w-full px-4 py-3 text-left hover:bg-blue-50 border-b border-gray-100 flex items-center"
              >
                <span className="text-lg mr-3">{mainCategory.icon || '📁'}</span>
                <div>
                  <div className="font-semibold text-gray-800">{mainCategory.name}</div>
                  <div className="text-xs text-gray-500">
                    {mainCategory.subcategories?.length || 0} subcategorias
                  </div>
                </div>
              </button>

              {/* Subcategories */}
              {mainCategory.subcategories?.map((subCategory) => (
                <button
                  key={subCategory.id}
                  type="button"
                  onClick={() => handleCategorySelect(subCategory)}
                  className="w-full px-8 py-2 text-left hover:bg-gray-50 text-gray-700 flex items-center border-l-2 border-gray-200 ml-4"
                >
                  <span className="text-sm mr-2">📄</span>
                  <span className="text-sm">{subCategory.name}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// AI Category Suggestion Component
const AICategorySuggestion = ({ description, onSuggestionSelect }) => {
  const [suggestion, setSuggestion] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (description && description.length > 3) {
      const debounceTimer = setTimeout(async () => {
        setLoading(true);
        try {
          const response = await axios.post(`${API}/categories/ai-classify`, {
            description: description
          });
          
          if (response.data.suggested_category && response.data.confidence > 0.3) {
            setSuggestion(response.data);
          } else {
            setSuggestion(null);
          }
        } catch (error) {
          console.error('AI suggestion error:', error);
          setSuggestion(null);
        }
        setLoading(false);
      }, 1000);

      return () => clearTimeout(debounceTimer);
    }
  }, [description]);

  if (!suggestion || loading) return null;

  return (
    <div className="mt-2 p-3 bg-purple-50 border border-purple-200 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-purple-600 mr-2">🤖</span>
          <div>
            <div className="text-sm font-medium text-purple-800">
              Sugestão da IA: {suggestion.suggested_category.name}
            </div>
            <div className="text-xs text-purple-600">
              {suggestion.suggested_category.parent_category_name && 
                `${suggestion.suggested_category.parent_category_name} → `}
              Confiança: {(suggestion.confidence * 100).toFixed(0)}%
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onSuggestionSelect(suggestion.suggested_category)}
          className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700"
        >
          Usar
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// 🧠 COMPONENTES DE IA - SISTEMA INTELIGENTE
// ============================================================================

const AIView = ({ insights, onRefreshInsights, onOpenChat, onOpenInsights }) => {
  const [prediction, setPrediction] = useState(null);
  
  useEffect(() => {
    // Carregar previsão de saldo
    const loadPrediction = async () => {
      try {
        const response = await axios.post(`${API}/ai/predict-balance`, { days_ahead: 30 });
        setPrediction(response.data);
      } catch (error) {
        console.error('Erro ao carregar previsão:', error);
      }
    };
    loadPrediction();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">🧠 Inteligência Artificial Financeira</h2>
        <p className="text-purple-100">Insights inteligentes e previsões para suas finanças</p>
      </div>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div 
          onClick={onOpenChat}
          className="bg-white rounded-xl p-6 shadow-lg border hover:shadow-xl transition-all cursor-pointer"
        >
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-lg font-semibold mb-2">Assistente Virtual</h3>
          <p className="text-gray-600 text-sm">Converse com nossa IA sobre suas finanças</p>
        </div>

        <div 
          onClick={onOpenInsights}
          className="bg-white rounded-xl p-6 shadow-lg border hover:shadow-xl transition-all cursor-pointer"
        >
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-lg font-semibold mb-2">Insights Inteligentes</h3>
          <p className="text-gray-600 text-sm">Análises automáticas dos seus gastos</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="text-4xl mb-4">🔮</div>
          <h3 className="text-lg font-semibold mb-2">Previsão de Saldo</h3>
          <p className="text-gray-600 text-sm mb-4">Próximo mês</p>
          {prediction && (
            <div className={`text-2xl font-bold ${prediction.predicted_balance > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(prediction.predicted_balance)}
            </div>
          )}
        </div>
      </div>

      {/* Recent Insights */}
      <div className="bg-white rounded-2xl p-6 shadow-lg border">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold">Insights Recentes</h3>
          <button 
            onClick={onRefreshInsights}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Atualizar
          </button>
        </div>
        
        {insights.length > 0 ? (
          <div className="space-y-4">
            {insights.slice(0, 5).map((insight, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800 mb-1">{insight.title}</h4>
                    <p className="text-gray-600 text-sm mb-2">{insight.description}</p>
                    <div className="flex items-center text-xs text-gray-500">
                      <span className={`px-2 py-1 rounded ${
                        insight.confidence > 0.8 ? 'bg-green-100 text-green-800' :
                        insight.confidence > 0.6 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {(insight.confidence * 100).toFixed(0)}% confiança
                      </span>
                    </div>
                  </div>
                  {insight.actionable && (
                    <div className="ml-4">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        Ação recomendada
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-4">🤖</div>
            <p>Nenhum insight disponível no momento.</p>
            <p className="text-sm">Use o sistema por alguns dias para gerar análises.</p>
          </div>
        )}
      </div>
    </div>
  );
};

const AIChatModal = ({ messages, onClose, onSendMessage }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!inputMessage.trim()) return;
    
    setIsLoading(true);
    await onSendMessage(inputMessage);
    setInputMessage('');
    setIsLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-t-2xl">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">🤖 Assistente Financeiro IA</h2>
            <button onClick={onClose} className="text-white hover:text-gray-200">✕</button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <div className="text-4xl mb-4">🤖</div>
                <p>Olá! Como posso te ajudar hoje?</p>
                <p className="text-sm mt-2">Pergunte sobre seu saldo, gastos, metas ou previsões!</p>
              </div>
            )}
            
            {messages.map((msg, index) => (
              <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  msg.type === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="p-6 border-t">
          <div className="flex items-center space-x-4">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Digite sua pergunta..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !inputMessage.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '...' : 'Enviar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const AIInsightsModal = ({ insights, onClose, onRefresh }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
      {/* Header */}
      <div className="p-6 border-b bg-gradient-to-r from-purple-600 to-blue-600 text-white">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">📊 Insights Inteligentes</h2>
          <div className="flex items-center space-x-4">
            <button onClick={onRefresh} className="text-white hover:text-gray-200">🔄 Atualizar</button>
            <button onClick={onClose} className="text-white hover:text-gray-200">✕</button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {insights.length > 0 ? (
          <div className="space-y-6">
            {insights.map((insight, index) => (
              <div key={index} className="border rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className={`w-4 h-4 rounded-full mr-3 ${
                      insight.type === 'prediction' ? 'bg-blue-500' :
                      insight.type === 'anomaly' ? 'bg-red-500' :
                      insight.type === 'suggestion' ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}></div>
                    <div>
                      <h3 className="text-lg font-semibold">{insight.title}</h3>
                      <span className="text-sm text-gray-500 capitalize">{insight.type}</span>
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded text-sm ${
                    insight.confidence > 0.8 ? 'bg-green-100 text-green-800' :
                    insight.confidence > 0.6 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {(insight.confidence * 100).toFixed(0)}% confiança
                  </div>
                </div>
                
                <p className="text-gray-700 mb-4">{insight.description}</p>
                
                {insight.actionable && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-blue-800 font-medium">💡 Ação Recomendada</p>
                    <p className="text-blue-700 text-sm mt-1">
                      Considere revisar este padrão e ajustar seus hábitos financeiros.
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🤖</div>
            <h3 className="text-xl mb-2">Nenhum insight disponível</h3>
            <p>Continue usando o sistema para gerar análises inteligentes!</p>
          </div>
        )}
      </div>
    </div>
  </div>
);

// ============================================================================
// 🏠 COMPONENTES DE CONSÓRCIO
// ============================================================================

const ConsortiumView = ({ consortiums, onRefresh, onCreateNew, onViewDetails }) => (
  <div className="space-y-6">
    {/* Header */}
    <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-6 text-white">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold mb-2">🏠 Controle de Consórcios</h2>
          <p className="text-green-100">Gerencie seus consórcios de imóveis e veículos</p>
        </div>
        <button
          onClick={onCreateNew}
          className="bg-white text-green-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
        >
          + Novo Consórcio
        </button>
      </div>
    </div>

    {/* Statistics Cards */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="bg-white rounded-xl p-6 shadow-lg border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Total de Consórcios</p>
            <p className="text-2xl font-bold text-gray-800">{consortiums.length}</p>
          </div>
          <div className="text-3xl">🏠</div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-lg border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Ativos</p>
            <p className="text-2xl font-bold text-green-600">
              {consortiums.filter(c => c.status === 'Ativo').length}
            </p>
          </div>
          <div className="text-3xl">✅</div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-lg border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Contemplados</p>
            <p className="text-2xl font-bold text-blue-600">
              {consortiums.filter(c => c.contemplated).length}
            </p>
          </div>
          <div className="text-3xl">🎉</div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-lg border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Valor Total</p>
            <p className="text-2xl font-bold text-purple-600">
              {formatCurrency(consortiums.reduce((sum, c) => sum + c.total_value, 0))}
            </p>
          </div>
          <div className="text-3xl">💰</div>
        </div>
      </div>
    </div>

    {/* Consortiums List */}
    <div className="bg-white rounded-2xl shadow-lg border">
      <div className="p-6 border-b">
        <h3 className="text-xl font-semibold">Meus Consórcios</h3>
      </div>
      
      <div className="p-6">
        {consortiums.length > 0 ? (
          <div className="space-y-4">
            {consortiums.map((consortium) => {
              const progress = (consortium.paid_installments / consortium.installment_count) * 100;
              
              return (
                <div key={consortium.id} className="border rounded-lg p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div className={`text-3xl ${
                        consortium.type === 'Imóvel' ? '🏠' :
                        consortium.type === 'Veículo' ? '🚗' : '🏍️'
                      }`}>
                        {consortium.type === 'Imóvel' ? '🏠' :
                         consortium.type === 'Veículo' ? '🚗' : '🏍️'}
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold">{consortium.name}</h4>
                        <p className="text-gray-600 text-sm">
                          {consortium.type} • {consortium.administrator}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className={`px-3 py-1 rounded-full text-sm ${
                        consortium.contemplated ? 'bg-green-100 text-green-800' :
                        consortium.status === 'Ativo' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {consortium.contemplated ? 'Contemplado' : consortium.status}
                      </div>
                      <button
                        onClick={() => onViewDetails(consortium.id)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Ver Detalhes
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-gray-600 text-sm">Valor da Carta</p>
                      <p className="font-semibold">{formatCurrency(consortium.total_value)}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 text-sm">Parcelas Pagas</p>
                      <p className="font-semibold">
                        {consortium.paid_installments} / {consortium.installment_count}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 text-sm">Saldo Devedor</p>
                      <p className="font-semibold text-red-600">
                        {formatCurrency(consortium.remaining_balance)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 text-sm">Parcela Mensal</p>
                      <p className="font-semibold">{formatCurrency(consortium.monthly_installment)}</p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600">Progresso</span>
                      <span className="font-medium">{progress.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(progress, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🏠</div>
            <h3 className="text-xl mb-2">Nenhum consórcio cadastrado</h3>
            <p className="mb-6">Comece adicionando seus consórcios para acompanhar o progresso</p>
            <button
              onClick={onCreateNew}
              className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700"
            >
              + Adicionar Primeiro Consórcio
            </button>
          </div>
        )}
      </div>
    </div>
  </div>
);

// ============================================================================
// 💳 CREDIT CARD INVOICE COMPONENTS
// ============================================================================

const CreditCardView = ({ invoices, loading, onRefresh, onGenerate, onPay }) => {
  const [paymentModal, setPaymentModal] = useState(null); // Stores invoice data for payment
  const [paymentAmount, setPaymentAmount] = useState('');

  const handlePayInvoice = () => {
    if (paymentModal && paymentAmount) {
      const amount = parseFloat(paymentAmount.replace(',', '.'));
      if (amount > 0) {
        onPay(paymentModal.id, amount);
        setPaymentModal(null);
        setPaymentAmount('');
      }
    }
  };

  // Get credit card accounts for display
  const creditCardAccounts = invoices.reduce((acc, invoice) => {
    if (!acc[invoice.account_id]) {
      acc[invoice.account_id] = {
        name: invoice.account_name,
        color: invoice.account_color,
        invoices: []
      };
    }
    acc[invoice.account_id].invoices.push(invoice);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold mb-2">💳 Gestão de Cartões</h2>
            <p className="text-orange-100">
              Controle completo das suas faturas de cartão de crédito
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onGenerate}
              className="bg-white text-orange-600 px-4 py-2 rounded-lg hover:bg-orange-50 transition-colors font-medium"
            >
              🔄 Gerar Faturas
            </button>
            <button
              onClick={onRefresh}
              disabled={loading}
              className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-400 transition-colors font-medium disabled:bg-orange-300"
            >
              {loading ? 'Carregando...' : '🔍 Atualizar'}
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total de Faturas</p>
              <p className="text-2xl font-bold text-gray-900">{invoices.length}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <CreditCard className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Pendentes</p>
              <p className="text-2xl font-bold text-orange-600">
                {invoices.filter(inv => inv.status === 'Pending').length}
              </p>
            </div>
            <div className="p-3 bg-orange-100 rounded-full">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Pagas</p>
              <p className="text-2xl font-bold text-green-600">
                {invoices.filter(inv => inv.status === 'Paid').length}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Valor Total</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(invoices.reduce((sum, inv) => sum + inv.total_amount, 0))}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <DollarSign className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Credit Card Accounts and Invoices */}
      {Object.keys(creditCardAccounts).length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center shadow-lg">
          <CreditCard className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Nenhuma fatura encontrada</h3>
          <p className="text-gray-600 mb-6">
            Clique em "Gerar Faturas" para criar as faturas dos seus cartões de crédito.
          </p>
          <button
            onClick={onGenerate}
            className="bg-orange-600 text-white px-6 py-3 rounded-lg hover:bg-orange-700 transition-colors font-medium"
          >
            🔄 Gerar Faturas Agora
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(creditCardAccounts).map(([accountId, accountData]) => (
            <div key={accountId} className="bg-white rounded-xl shadow-lg border overflow-hidden">
              {/* Account Header */}
              <div className="bg-gray-50 px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: accountData.color }}
                    ></div>
                    <h3 className="text-lg font-semibold text-gray-900">{accountData.name}</h3>
                    <span className="text-sm bg-gray-200 px-2 py-1 rounded">
                      {accountData.invoices.length} fatura{accountData.invoices.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Total em aberto</p>
                    <p className="text-lg font-bold text-orange-600">
                      {formatCurrency(
                        accountData.invoices
                          .filter(inv => inv.status !== 'Paid')
                          .reduce((sum, inv) => sum + (inv.total_amount - inv.paid_amount), 0)
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* Invoices List */}
              <div className="divide-y divide-gray-200">
                {accountData.invoices
                  .sort((a, b) => new Date(b.due_date) - new Date(a.due_date))
                  .map((invoice) => {
                    const isOverdue = new Date(invoice.due_date) < new Date() && invoice.status !== 'Paid';
                    const remainingAmount = invoice.total_amount - invoice.paid_amount;
                    
                    return (
                      <div key={invoice.id} className="px-6 py-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className={`p-2 rounded-full ${
                              invoice.status === 'Paid' ? 'bg-green-100' :
                              isOverdue ? 'bg-red-100' : 'bg-orange-100'
                            }`}>
                              {invoice.status === 'Paid' ? (
                                <CheckCircle className="w-5 h-5 text-green-600" />
                              ) : isOverdue ? (
                                <AlertTriangle className="w-5 h-5 text-red-600" />
                              ) : (
                                <Clock className="w-5 h-5 text-orange-600" />
                              )}
                            </div>
                            
                            <div>
                              <h4 className="font-medium text-gray-900">
                                Fatura {invoice.invoice_month}
                              </h4>
                              <p className="text-sm text-gray-600">
                                Vencimento: {formatDate(invoice.due_date)}
                                {isOverdue && <span className="text-red-600 font-medium ml-2">• Vencida</span>}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center space-x-4">
                            <div className="text-right">
                              <p className={`font-bold ${
                                invoice.status === 'Paid' ? 'text-green-600' : 'text-gray-900'
                              }`}>
                                {formatCurrency(invoice.total_amount)}
                              </p>
                              {invoice.paid_amount > 0 && invoice.status !== 'Paid' && (
                                <p className="text-sm text-gray-600">
                                  Pago: {formatCurrency(invoice.paid_amount)}
                                </p>
                              )}
                              {remainingAmount > 0 && invoice.status !== 'Paid' && (
                                <p className="text-sm text-orange-600 font-medium">
                                  Restante: {formatCurrency(remainingAmount)}
                                </p>
                              )}
                            </div>

                            {invoice.status !== 'Paid' && (
                              <button
                                onClick={() => {
                                  setPaymentModal(invoice);
                                  setPaymentAmount(remainingAmount.toFixed(2).replace('.', ','));
                                }}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                  isOverdue 
                                    ? 'bg-red-600 text-white hover:bg-red-700' 
                                    : 'bg-orange-600 text-white hover:bg-orange-700'
                                }`}
                              >
                                💳 Pagar
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Transaction count */}
                        {invoice.transactions.length > 0 && (
                          <div className="mt-3 ml-12">
                            <p className="text-sm text-gray-600">
                              {invoice.transactions.length} transação{invoice.transactions.length !== 1 ? 'ões' : ''} incluída{invoice.transactions.length !== 1 ? 's' : ''}
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Payment Modal */}
      {paymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900">💳 Pagar Fatura</h3>
              <button
                onClick={() => setPaymentModal(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600">Cartão</p>
                <p className="font-medium text-gray-900">{paymentModal.account_name}</p>
              </div>

              <div>
                <p className="text-sm text-gray-600">Fatura</p>
                <p className="font-medium text-gray-900">
                  {paymentModal.invoice_month} • Vencimento: {formatDate(paymentModal.due_date)}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600">Valor da Fatura</p>
                <p className="text-lg font-bold text-gray-900">
                  {formatCurrency(paymentModal.total_amount)}
                </p>
                {paymentModal.paid_amount > 0 && (
                  <p className="text-sm text-gray-600">
                    Já pago: {formatCurrency(paymentModal.paid_amount)}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valor do Pagamento
                </label>
                <input
                  type="text"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  placeholder="0,00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-orange-500"
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setPaymentModal(null)}
                className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handlePayInvoice}
                className="flex-1 bg-orange-600 text-white py-2 rounded-lg hover:bg-orange-700 transition-colors"
              >
                Confirmar Pagamento
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ConsortiumModal = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'Imóvel',
    total_value: 0,
    installment_count: 240,
    paid_installments: 0,
    due_day: 15,
    start_date: new Date().toISOString().split('T')[0],
    administrator: '',
    group_number: '',
    quota_number: '',
    bid_value: 0,
    notes: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-green-600 to-emerald-600 text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">🏠 Novo Consórcio</h2>
            <button onClick={onClose} className="text-white hover:text-gray-200">✕</button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Nome */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Nome do Consórcio *</label>
              <input
                type="text"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Ex: Consórcio Casa Própria"
              />
            </div>

            {/* Tipo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tipo *</label>
              <select
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.type}
                onChange={(e) => setFormData({...formData, type: e.target.value})}
              >
                <option value="Imóvel">🏠 Imóvel</option>
                <option value="Veículo">🚗 Veículo</option>
                <option value="Moto">🏍️ Moto</option>
              </select>
            </div>

            {/* Valor da Carta */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valor da Carta *</label>
              <BrazilianCurrencyInput
                value={formData.total_value}
                onChange={(value) => setFormData({...formData, total_value: value})}
                placeholder="R$ 300.000,00"
                required
              />
            </div>

            {/* Parcelas Totais */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Parcelas Totais *</label>
              <input
                type="number"
                required
                min="1"
                max="300"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.installment_count}
                onChange={(e) => setFormData({...formData, installment_count: parseInt(e.target.value)})}
              />
            </div>

            {/* Parcelas Já Pagas */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Parcelas Já Pagas</label>
              <input
                type="number"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.paid_installments}
                onChange={(e) => setFormData({...formData, paid_installments: parseInt(e.target.value)})}
              />
            </div>

            {/* Administradora */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Administradora *</label>
              <select
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.administrator}
                onChange={(e) => setFormData({...formData, administrator: e.target.value})}
              >
                <option value="">Selecione...</option>
                <option value="Bradesco">Bradesco Consórcios</option>
                <option value="Santander">Santander Consórcios</option>
                <option value="Itaú">Itaú Consórcios</option>
                <option value="Caixa">Caixa Consórcios</option>
                <option value="Banco do Brasil">BB Consórcios</option>
                <option value="Honda">Honda Consórcios</option>
                <option value="Volkswagen">Volkswagen Consórcios</option>
                <option value="Rodobens">Rodobens Consórcios</option>
                <option value="Outro">Outro</option>
              </select>
            </div>

            {/* Grupo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Número do Grupo</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.group_number}
                onChange={(e) => setFormData({...formData, group_number: e.target.value})}
                placeholder="Ex: 001"
              />
            </div>

            {/* Cota */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Número da Cota</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.quota_number}
                onChange={(e) => setFormData({...formData, quota_number: e.target.value})}
                placeholder="Ex: 025"
              />
            </div>

            {/* Data de Início */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Data de Início *</label>
              <input
                type="date"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.start_date}
                onChange={(e) => setFormData({...formData, start_date: e.target.value})}
              />
            </div>

            {/* Dia do Vencimento */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dia do Vencimento</label>
              <input
                type="number"
                min="1"
                max="31"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500"
                value={formData.due_day}
                onChange={(e) => setFormData({...formData, due_day: parseInt(e.target.value)})}
              />
            </div>

            {/* Valor do Lance */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valor do Lance (opcional)</label>
              <BrazilianCurrencyInput
                value={formData.bid_value}
                onChange={(value) => setFormData({...formData, bid_value: value})}
                placeholder="R$ 0,00"
              />
            </div>
          </div>

          {/* Observações */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Observações</label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200"
              rows="3"
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Observações adicionais sobre o consórcio..."
            ></textarea>
          </div>

          {/* Botões */}
          <div className="flex justify-end space-x-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Criar Consórcio
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ConsortiumDetailsModal = ({ consortium, onClose, onPayment, onMarkContemplation }) => {
  const [showPaymentForm, setShowPaymentForm] = useState(false);

  if (!consortium) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-green-600 to-emerald-600 text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">🏠 Detalhes do Consórcio</h2>
            <button onClick={onClose} className="text-white hover:text-gray-200">✕</button>
          </div>
        </div>

        <div className="p-6">
          {/* Consortium Info */}
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold mb-4">{consortium.consortium?.name}</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-gray-600 text-sm">Tipo</p>
                <p className="font-semibold">{consortium.consortium?.type}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Status</p>
                <p className={`font-semibold ${
                  consortium.consortium?.contemplated ? 'text-green-600' : 'text-blue-600'
                }`}>
                  {consortium.consortium?.contemplated ? 'Contemplado' : consortium.consortium?.status}
                </p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Administradora</p>
                <p className="font-semibold">{consortium.consortium?.administrator}</p>
              </div>
              <div>
                <p className="text-gray-600 text-sm">Grupo/Cota</p>
                <p className="font-semibold">
                  {consortium.consortium?.group_number} / {consortium.consortium?.quota_number}
                </p>
              </div>
            </div>

            {/* Progress */}
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-2">
                <span>Progresso do Pagamento</span>
                <span className="font-medium">
                  {consortium.statistics?.progress_percentage?.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-gradient-to-r from-green-400 to-green-600 h-4 rounded-full"
                  style={{ width: `${Math.min(consortium.statistics?.progress_percentage || 0, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white border rounded-lg p-4">
              <p className="text-gray-600 text-sm">Valor da Carta</p>
              <p className="text-xl font-bold text-green-600">
                {formatCurrency(consortium.consortium?.total_value || 0)}
              </p>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <p className="text-gray-600 text-sm">Total Pago</p>
              <p className="text-xl font-bold text-blue-600">
                {formatCurrency(consortium.statistics?.total_paid || 0)}
              </p>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <p className="text-gray-600 text-sm">Saldo Devedor</p>
              <p className="text-xl font-bold text-red-600">
                {formatCurrency(consortium.consortium?.remaining_balance || 0)}
              </p>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <p className="text-gray-600 text-sm">Parcelas Restantes</p>
              <p className="text-xl font-bold text-purple-600">
                {consortium.statistics?.remaining_installments || 0}
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => setShowPaymentForm(true)}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              💳 Registrar Pagamento
            </button>
            
            {!consortium.consortium?.contemplated && (
              <button
                onClick={() => onMarkContemplation(consortium.consortium?.id)}
                className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700"
              >
                🎉 Marcar como Contemplado
              </button>
            )}
          </div>

          {/* Payment History */}
          <div className="bg-white border rounded-lg p-6">
            <h4 className="text-lg font-semibold mb-4">Histórico de Pagamentos</h4>
            
            {consortium.payments && consortium.payments.length > 0 ? (
              <div className="space-y-3">
                {consortium.payments.map((payment, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="text-green-600">✅</div>
                      <div>
                        <p className="font-medium">Parcela #{payment.installment_number}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(payment.payment_date).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{formatCurrency(payment.amount_paid)}</p>
                      <p className="text-sm text-gray-600">{payment.payment_type}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>Nenhum pagamento registrado</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Payment Form Modal */}
      {showPaymentForm && (
        <PaymentFormModal
          consortiumId={consortium.consortium?.id}
          onClose={() => setShowPaymentForm(false)}
          onSubmit={onPayment}
        />
      )}
    </div>
  );
};

const PaymentFormModal = ({ consortiumId, onClose, onSubmit }) => {
  const [paymentData, setPaymentData] = useState({
    installment_number: 1,
    payment_date: new Date().toISOString().split('T')[0],
    amount_paid: 0,
    payment_type: 'Regular',
    notes: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(consortiumId, paymentData);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-60">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold">💳 Registrar Pagamento</h3>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Número da Parcela</label>
            <input
              type="number"
              min="1"
              required
              className="w-full px-3 py-2 border rounded-lg"
              value={paymentData.installment_number}
              onChange={(e) => setPaymentData({...paymentData, installment_number: parseInt(e.target.value)})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Data do Pagamento</label>
            <input
              type="date"
              required
              className="w-full px-3 py-2 border rounded-lg"
              value={paymentData.payment_date}
              onChange={(e) => setPaymentData({...paymentData, payment_date: e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Valor Pago</label>
            <BrazilianCurrencyInput
              value={paymentData.amount_paid}
              onChange={(value) => setPaymentData({...paymentData, amount_paid: value})}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Tipo de Pagamento</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={paymentData.payment_type}
              onChange={(e) => setPaymentData({...paymentData, payment_type: e.target.value})}
            >
              <option value="Regular">Regular</option>
              <option value="Antecipado">Antecipado</option>
              <option value="Lance">Lance</option>
              <option value="Quitação">Quitação</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Observações</label>
            <textarea
              className="w-full px-3 py-2 border rounded-lg"
              rows="2"
              value={paymentData.notes}
              onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Registrar
            </button>
          </div>
        </form>
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
};

// 👤 Profile View Component
const ProfileView = ({ user, onRefresh, onEditProfile, onChangePassword }) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg border p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">👤 Perfil do Usuário</h1>
            <p className="text-gray-600 mt-1">Gerencie suas informações pessoais e configurações de conta</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onEditProfile}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Edit className="w-4 h-4" />
              Editar Perfil
            </button>
            <button
              onClick={onChangePassword}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
            >
              <Settings className="w-4 h-4" />
              Alterar Senha
            </button>
          </div>
        </div>
      </div>

      {/* User Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Personal Information */}
        <div className="bg-white rounded-xl shadow-lg border">
          <div className="p-6">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-blue-100 rounded-full mr-4">
                <Settings className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Informações Pessoais</h3>
                <p className="text-gray-600 text-sm">Dados da sua conta</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Completo</label>
                <div className="p-3 bg-gray-50 rounded-lg border">
                  <p className="text-gray-900 font-medium">{user?.name || 'Não informado'}</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <div className="p-3 bg-gray-50 rounded-lg border">
                  <p className="text-gray-900 font-medium">{user?.email || 'Não informado'}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status da Conta</label>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm text-green-600 font-medium">Ativa</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Account Security */}
        <div className="bg-white rounded-xl shadow-lg border">
          <div className="p-6">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-purple-100 rounded-full mr-4">
                <Settings className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Segurança da Conta</h3>
                <p className="text-gray-600 text-sm">Configurações de segurança</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="font-medium text-gray-900">Senha da Conta</h4>
                    <p className="text-sm text-gray-600">Última alteração há mais de 30 dias</p>
                  </div>
                  <button
                    onClick={onChangePassword}
                    className="text-purple-600 hover:text-purple-800 font-medium text-sm"
                  >
                    Alterar
                  </button>
                </div>
              </div>

              <div className="p-4 border rounded-lg bg-gray-50">
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="font-medium text-gray-900">Verificação por Email</h4>
                    <p className="text-sm text-gray-600">Email verificado com sucesso</p>
                  </div>
                  <div className="text-green-600">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Activity Summary */}
      <div className="bg-white rounded-xl shadow-lg border">
        <div className="p-6">
          <div className="flex items-center mb-6">
            <div className="p-3 bg-indigo-100 rounded-full mr-4">
              <Bell className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Resumo da Atividade</h3>
              <p className="text-gray-600 text-sm">Estatísticas da sua conta</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600 mb-1">
                {new Date().toLocaleDateString('pt-BR').split('/')[2]}
              </div>
              <div className="text-sm text-blue-800">Membro desde</div>
            </div>
            
            <div className="p-4 bg-green-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-600 mb-1">✓</div>
              <div className="text-sm text-green-800">Conta Verificada</div>
            </div>
            
            <div className="p-4 bg-purple-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-purple-600 mb-1">🔒</div>
              <div className="text-sm text-purple-800">Dados Protegidos</div>
            </div>
            
            <div className="p-4 bg-orange-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-orange-600 mb-1">🎯</div>
              <div className="text-sm text-orange-800">Perfil Ativo</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Profile Modal Component
const ProfileModal = ({ profileData, onClose, onUpdate, onProfileDataChange }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onUpdate(e);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
        <div className="px-6 py-4 border-b border-gray-200 rounded-t-xl">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">✏️ Editar Perfil</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nome Completo *
            </label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={profileData.name}
              onChange={(e) => onProfileDataChange({...profileData, name: e.target.value})}
              placeholder="Digite seu nome completo"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email *
            </label>
            <input
              type="email"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
              value={profileData.email}
              onChange={(e) => onProfileDataChange({...profileData, email: e.target.value})}
              placeholder="seu@email.com"
            />
            <p className="text-xs text-gray-500 mt-1">
              Se alterar o email, será necessário verificá-lo novamente
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
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Salvar Alterações
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Password Modal Component
const PasswordModal = ({ passwordData, onClose, onChange, onPasswordDataChange }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onChange(e);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
        <div className="px-6 py-4 border-b border-gray-200 rounded-t-xl">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">🔒 Alterar Senha</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Senha Atual *
            </label>
            <input
              type="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
              value={passwordData.current_password}
              onChange={(e) => onPasswordDataChange({...passwordData, current_password: e.target.value})}
              placeholder="Digite sua senha atual"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nova Senha *
            </label>
            <input
              type="password"
              required
              minLength={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
              value={passwordData.new_password}
              onChange={(e) => onPasswordDataChange({...passwordData, new_password: e.target.value})}
              placeholder="Digite sua nova senha"
            />
            <p className="text-xs text-gray-500 mt-1">
              A senha deve ter pelo menos 6 caracteres
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirmar Nova Senha *
            </label>
            <input
              type="password"
              required
              minLength={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
              value={passwordData.confirm_password}
              onChange={(e) => onPasswordDataChange({...passwordData, confirm_password: e.target.value})}
              placeholder="Confirme sua nova senha"
            />
            {passwordData.new_password && passwordData.confirm_password && 
             passwordData.new_password !== passwordData.confirm_password && (
              <p className="text-xs text-red-500 mt-1">
                As senhas não coincidem
              </p>
            )}
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
              disabled={
                !passwordData.current_password || 
                !passwordData.new_password || 
                !passwordData.confirm_password ||
                passwordData.new_password !== passwordData.confirm_password
              }
            >
              Alterar Senha
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// 📄 File Import View Component
const FileImportView = ({ 
  importStep, 
  selectedFiles, 
  importPreview, 
  selectedTransactions, 
  importLoading, 
  onFileUpload, 
  onImportConfirm, 
  onTransactionToggle, 
  onReset 
}) => {
  const fileInputRef = React.useRef(null);

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileUpload(files);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR');
    } catch {
      return dateString;
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📄 Importar Arquivos</h1>
        <p className="text-gray-600">
          Importe transações de arquivos CSV, Excel, PDF ou imagens
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`flex items-center ${importStep === 'upload' ? 'text-blue-600' : importStep === 'confirming' ? 'text-gray-400' : 'text-green-600'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold mr-3 ${
              importStep === 'upload' ? 'bg-blue-100 text-blue-600' : 
              importStep === 'confirming' ? 'bg-gray-100 text-gray-400' : 
              'bg-green-100 text-green-600'
            }`}>
              1
            </div>
            <span className="font-medium">Upload</span>
          </div>
          
          <div className={`flex items-center ${importStep === 'preview' ? 'text-blue-600' : importStep === 'upload' ? 'text-gray-400' : 'text-green-600'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold mr-3 ${
              importStep === 'preview' ? 'bg-blue-100 text-blue-600' : 
              importStep === 'upload' ? 'bg-gray-100 text-gray-400' : 
              'bg-green-100 text-green-600'
            }`}>
              2
            </div>
            <span className="font-medium">Preview</span>
          </div>
          
          <div className={`flex items-center ${importStep === 'confirming' ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold mr-3 ${
              importStep === 'confirming' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'
            }`}>
              3
            </div>
            <span className="font-medium">Confirmar</span>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ 
              width: importStep === 'upload' ? '33%' : 
                     importStep === 'preview' ? '66%' : '100%' 
            }}
          ></div>
        </div>
      </div>

      {/* Upload Step */}
      {importStep === 'upload' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="text-center">
            <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Selecione os arquivos</h3>
            <p className="text-gray-600 mb-6">
              Formatos suportados: .xlsx, .csv, .pdf, .jpg, .png
            </p>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".xlsx,.csv,.pdf,.jpg,.jpeg,.png"
              onChange={handleFileSelect}
              className="hidden"
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={importLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {importLoading ? 'Processando...' : 'Selecionar Arquivos'}
            </button>
            
            <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
              <div className="flex items-center justify-center p-3 bg-green-50 rounded-lg">
                <FileText className="w-5 h-5 text-green-600 mr-2" />
                Excel/CSV
              </div>
              <div className="flex items-center justify-center p-3 bg-red-50 rounded-lg">
                <FileText className="w-5 h-5 text-red-600 mr-2" />
                PDF
              </div>
              <div className="flex items-center justify-center p-3 bg-blue-50 rounded-lg">
                <Upload className="w-5 h-5 text-blue-600 mr-2" />
                JPG
              </div>
              <div className="flex items-center justify-center p-3 bg-purple-50 rounded-lg">
                <Upload className="w-5 h-5 text-purple-600 mr-2" />
                PNG
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Step */}
      {importStep === 'preview' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Preview das Transações</h3>
                <p className="text-sm text-gray-600">
                  {importPreview.length} transação(es) encontrada(s) • {selectedTransactions.length} selecionada(s)
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={onReset}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={onImportConfirm}
                  disabled={selectedTransactions.length === 0 || importLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {importLoading ? 'Importando...' : `Importar ${selectedTransactions.length} Transação(ões)`}
                </button>
              </div>
            </div>
          </div>

          <div className="p-6">
            {importPreview.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Nenhuma transação encontrada nos arquivos.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {importPreview.map((transaction, index) => {
                  const isSelected = selectedTransactions.some(t => 
                    t.descricao === transaction.descricao && 
                    t.valor === transaction.valor && 
                    t.data === transaction.data
                  );
                  
                  return (
                    <div 
                      key={index}
                      className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all ${
                        isSelected 
                          ? 'border-green-500 bg-green-50' 
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => onTransactionToggle(transaction)}
                    >
                      <div className={`w-5 h-5 rounded border-2 mr-4 flex items-center justify-center ${
                        isSelected ? 'border-green-500 bg-green-500' : 'border-gray-300'
                      }`}>
                        {isSelected && <CheckCircle className="w-3 h-3 text-white" />}
                      </div>
                      
                      <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                          <p className="font-medium text-gray-900">{transaction.descricao}</p>
                          <p className="text-sm text-gray-500">{formatDate(transaction.data)}</p>
                        </div>
                        <div>
                          <p className={`font-semibold ${
                            transaction.tipo === 'Receita' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {formatCurrency(transaction.valor)}
                          </p>
                          <p className="text-sm text-gray-500">{transaction.tipo}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-700">{transaction.conta || 'Conta não especificada'}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-700">{transaction.categoria || 'Categoria não especificada'}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confirming Step */}
      {importStep === 'confirming' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Importando transações...</h3>
            <p className="text-gray-600">
              Aguarde enquanto processamos suas {selectedTransactions.length} transação(ões)
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// 🏠 Contracts View Component
const ContractsView = ({ 
  contracts, 
  contractStats, 
  contractFilters, 
  contractsLoading, 
  onLoadContracts, 
  onLoadStats,
  onFiltersChange, 
  onCreateContract, 
  onEditContract, 
  onDeleteContract 
}) => {
  React.useEffect(() => {
    onLoadContracts();
    onLoadStats();
  }, [contractFilters]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR');
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ativo': return 'bg-green-100 text-green-800';
      case 'quitado': return 'bg-blue-100 text-blue-800';
      case 'cancelado': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (tipo) => {
    return tipo === 'consórcio' ? '🏠' : '💼';
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">🏠 Contratos</h1>
            <p className="text-gray-600">
              Gerencie seus consórcios e empréstimos consignados
            </p>
          </div>
          <button
            onClick={() => onCreateContract()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Novo Contrato
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100">
              <FileText className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total de Contratos</p>
              <p className="text-2xl font-bold text-gray-900">{contractStats.total_contracts || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Contratos Ativos</p>
              <p className="text-2xl font-bold text-gray-900">{contractStats.active_contracts || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Valor Total</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(contractStats.total_value_sum || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-orange-100">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Valor Restante</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(contractStats.total_remaining_sum || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Filtros</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo</label>
            <select
              value={contractFilters.tipo}
              onChange={(e) => onFiltersChange({ ...contractFilters, tipo: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
            >
              <option value="">Todos os tipos</option>
              <option value="consórcio">Consórcio</option>
              <option value="consignado">Empréstimo Consignado</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={contractFilters.status}
              onChange={(e) => onFiltersChange({ ...contractFilters, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
            >
              <option value="">Todos os status</option>
              <option value="ativo">Ativo</option>
              <option value="quitado">Quitado</option>
              <option value="cancelado">Cancelado</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => onFiltersChange({ tipo: '', status: '' })}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Limpar Filtros
            </button>
          </div>
        </div>
      </div>

      {/* Contracts List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Lista de Contratos</h3>
        </div>

        <div className="p-6">
          {contractsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
              <p className="text-gray-500 mt-4">Carregando contratos...</p>
            </div>
          ) : contracts.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum contrato encontrado</h3>
              <p className="text-gray-500 mb-4">Crie seu primeiro contrato para começar</p>
              <button
                onClick={() => onCreateContract()}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Criar Contrato
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {contracts.map((contract) => (
                <div 
                  key={contract.id}
                  className="border border-gray-200 rounded-lg p-6 hover:border-purple-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-2xl">{getTypeIcon(contract.tipo)}</span>
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900">{contract.nome}</h4>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500 capitalize">{contract.tipo}</span>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(contract.status)}`}>
                              {contract.status}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600">Valor Total</p>
                          <p className="font-semibold text-gray-900">{formatCurrency(contract.valor_total_final || 0)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Parcela Mensal</p>
                          <p className="font-semibold text-gray-900">{formatCurrency(contract.parcela_mensal)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Progresso</p>
                          <p className="font-semibold text-gray-900">
                            {contract.parcela_atual}/{contract.quantidade_parcelas} 
                            <span className="text-sm text-gray-500 ml-1">
                              ({(contract.progresso_percentual || 0).toFixed(1)}%)
                            </span>
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Vencimento</p>
                          <p className="font-semibold text-gray-900">{formatDate(contract.data_vencimento)}</p>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="mb-4">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                            style={{ 
                              width: `${Math.min(contract.progresso_percentual || 0, 100)}%` 
                            }}
                          ></div>
                        </div>
                      </div>

                      {contract.observacoes && (
                        <div className="bg-gray-50 rounded-lg p-3 mb-4">
                          <p className="text-sm text-gray-600">
                            <strong>Observações:</strong> {contract.observacoes}
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => onEditContract(contract)}
                        className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                        title="Editar contrato"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => onDeleteContract(contract.id)}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        title="Excluir contrato"
                      >
                        <Trash2 className="w-4 h-4" />
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
  );
};

// 🏠 Contract Modal Component
const ContractModal = ({ contract, onClose, onCreate, onUpdate }) => {
  const [formData, setFormData] = useState({
    tipo: 'consórcio',
    nome: '',
    valor_total: '',
    parcela_mensal: '',
    quantidade_parcelas: '',
    parcela_atual: '0',
    juros_mensal: '',
    taxa_administrativa: '',
    seguro: '',
    data_inicio: '',
    data_vencimento: '',
    status: 'ativo',
    observacoes: ''
  });

  React.useEffect(() => {
    if (contract) {
      setFormData({
        tipo: contract.tipo || 'consórcio',
        nome: contract.nome || '',
        valor_total: contract.valor_total?.toString() || '',
        parcela_mensal: contract.parcela_mensal?.toString() || '',
        quantidade_parcelas: contract.quantidade_parcelas?.toString() || '',
        parcela_atual: contract.parcela_atual?.toString() || '0',
        juros_mensal: contract.juros_mensal?.toString() || '',
        taxa_administrativa: contract.taxa_administrativa?.toString() || '',
        seguro: contract.seguro?.toString() || '',
        data_inicio: contract.data_inicio ? new Date(contract.data_inicio).toISOString().split('T')[0] : '',
        data_vencimento: contract.data_vencimento ? new Date(contract.data_vencimento).toISOString().split('T')[0] : '',
        status: contract.status || 'ativo',
        observacoes: contract.observacoes || ''
      });
    }
  }, [contract]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const contractData = {
      ...formData,
      valor_total: parseFloat(formData.valor_total),
      parcela_mensal: parseFloat(formData.parcela_mensal),
      quantidade_parcelas: parseInt(formData.quantidade_parcelas),
      parcela_atual: parseInt(formData.parcela_atual),
      juros_mensal: parseFloat(formData.juros_mensal),
      taxa_administrativa: parseFloat(formData.taxa_administrativa),
      seguro: parseFloat(formData.seguro),
      data_inicio: new Date(formData.data_inicio).toISOString(),
      data_vencimento: new Date(formData.data_vencimento).toISOString()
    };

    if (contract) {
      onUpdate(contract.id, contractData);
    } else {
      onCreate(contractData);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {contract ? 'Editar Contrato' : 'Novo Contrato'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Tipo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tipo *</label>
              <select
                required
                value={formData.tipo}
                onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
              >
                <option value="consórcio">Consórcio</option>
                <option value="consignado">Empréstimo Consignado</option>
              </select>
            </div>

            {/* Nome */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Nome do Contrato *</label>
              <input
                type="text"
                required
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="Ex: Consórcio Casa Própria"
              />
            </div>

            {/* Valor Total */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valor Total *</label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.valor_total}
                onChange={(e) => setFormData({ ...formData, valor_total: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="0.00"
              />
            </div>

            {/* Parcela Mensal */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Parcela Mensal *</label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.parcela_mensal}
                onChange={(e) => setFormData({ ...formData, parcela_mensal: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="0.00"
              />
            </div>

            {/* Quantidade de Parcelas */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Quantidade de Parcelas *</label>
              <input
                type="number"
                required
                value={formData.quantidade_parcelas}
                onChange={(e) => setFormData({ ...formData, quantidade_parcelas: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="240"
              />
            </div>

            {/* Parcela Atual */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Parcela Atual</label>
              <input
                type="number"
                value={formData.parcela_atual}
                onChange={(e) => setFormData({ ...formData, parcela_atual: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="0"
              />
            </div>

            {/* Juros Mensal */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Juros Mensal (%) *</label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.juros_mensal}
                onChange={(e) => setFormData({ ...formData, juros_mensal: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="1.2"
              />
            </div>

            {/* Taxa Administrativa */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Taxa Administrativa *</label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.taxa_administrativa}
                onChange={(e) => setFormData({ ...formData, taxa_administrativa: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="0.00"
              />
            </div>

            {/* Seguro */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Seguro *</label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.seguro}
                onChange={(e) => setFormData({ ...formData, seguro: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                placeholder="0.00"
              />
            </div>

            {/* Data de Início */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Data de Início *</label>
              <input
                type="date"
                required
                value={formData.data_inicio}
                onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
              />
            </div>

            {/* Data de Vencimento */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Data de Vencimento *</label>
              <input
                type="date"
                required
                value={formData.data_vencimento}
                onChange={(e) => setFormData({ ...formData, data_vencimento: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
              />
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
              >
                <option value="ativo">Ativo</option>
                <option value="quitado">Quitado</option>
                <option value="cancelado">Cancelado</option>
              </select>
            </div>
          </div>

          {/* Observações */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Observações</label>
            <textarea
              rows={4}
              value={formData.observacoes}
              onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
              placeholder="Observações adicionais sobre o contrato..."
            />
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-3 mt-6">
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
              {contract ? 'Atualizar' : 'Criar'} Contrato
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// 🐾 Pet Shop View Component
const PetShopView = () => {
  const [activeSubView, setActiveSubView] = useState('dashboard');
  const [products, setProducts] = useState([]);
  const [sales, setSales] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);

  // States para modais locais
  const [showProductModal, setShowProductModal] = useState(false);
  const [showSaleModal, setShowSaleModal] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [stockProduct, setStockProduct] = useState(null);
  const [currentReceipt, setCurrentReceipt] = useState(null);

  // Estados para filtros
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [supplierFilter, setSupplierFilter] = useState('');

  // Carregar dados
  const loadPetShopData = async () => {
    try {
      setLoading(true);
      
      const [productsRes, salesRes, statsRes] = await Promise.all([
        axios.get(`${API}/petshop/products`),
        axios.get(`${API}/petshop/sales`),
        axios.get(`${API}/petshop/statistics`)
      ]);

      setProducts(productsRes.data);
      setSales(salesRes.data);
      setStatistics(statsRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados do Pet Shop:', error);
      toast.error('Erro ao carregar dados do Pet Shop');
    } finally {
      setLoading(false);
    }
  };

  // Funções para gerenciar produtos
  const handleCreateProduct = async (productData) => {
    try {
      console.log('Creating product:', productData);
      const response = await axios.post(`${API}/petshop/products`, productData);
      
      toast.success('Produto criado com sucesso!');
      setShowProductModal(false);
      setEditingProduct(null);
      
      // Recarregar dados
      await loadPetShopData();
    } catch (error) {
      console.error('Erro ao criar produto:', error);
      if (error.response?.data?.detail?.includes('SKU')) {
        toast.error('SKU já existe! Use um código único.');
      } else {
        toast.error(error.response?.data?.detail || 'Erro ao criar produto');
      }
    }
  };

  const handleUpdateProduct = async (productId, productData) => {
    try {
      console.log('Updating product:', productId, productData);
      const response = await axios.put(`${API}/petshop/products/${productId}`, productData);
      
      toast.success('Produto atualizado com sucesso!');
      setShowProductModal(false);
      setEditingProduct(null);
      
      // Recarregar dados
      await loadPetShopData();
    } catch (error) {
      console.error('Erro ao atualizar produto:', error);
      if (error.response?.data?.detail?.includes('SKU')) {
        toast.error('SKU já existe! Use um código único.');
      } else {
        toast.error(error.response?.data?.detail || 'Erro ao atualizar produto');
      }
    }
  };

  // Função para deletar produto
  const handleDeleteProduct = async (productId, productName) => {
    if (window.confirm(`⚠️ ATENÇÃO: Tem certeza que deseja excluir o produto "${productName}"?\n\n🗑️ Esta ação:\n• Excluirá o produto permanentemente\n• Não pode ser desfeita\n\nDigite OK para confirmar.`)) {
      try {
        await axios.delete(`${API}/petshop/products/${productId}`);
        toast.success('Produto excluído com sucesso!');
        
        // Recarregar dados
        await loadPetShopData();
      } catch (error) {
        console.error('Erro ao excluir produto:', error);
        toast.error(error.response?.data?.detail || 'Erro ao excluir produto');
      }
    }
  };

  // Função para movimentação de estoque
  const handleStockMovement = async (movementData) => {
    try {
      console.log('Stock movement:', movementData);
      const response = await axios.post(`${API}/petshop/stock-movement`, movementData);
      
      toast.success(`${movementData.type === 'entrada' ? 'Entrada' : 'Saída'} de estoque registrada com sucesso!`);
      setShowStockModal(false);
      setStockProduct(null);
      
      // Recarregar dados
      await loadPetShopData();
    } catch (error) {
      console.error('Erro na movimentação de estoque:', error);
      toast.error(error.response?.data?.detail || 'Erro na movimentação de estoque');
    }
  };

  // Carregar dados na inicialização
  React.useEffect(() => {
    loadPetShopData();
  }, []);

  // Sub-navegação do Pet Shop
  const subNavItems = [
    { id: 'dashboard', label: '📊 Dashboard', icon: BarChart3 },
    { id: 'products', label: '📦 Produtos', icon: Package },
    { id: 'sales', label: '🛒 Vendas', icon: ShoppingCart },
    { id: 'stock-alert', label: '⚠️ Estoque Baixo', icon: AlertTriangle }
  ];

  return (
    <div className="space-y-6">
      {/* Header do Pet Shop */}
      <div className="bg-gradient-to-r from-pink-500 to-purple-600 rounded-2xl shadow-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="bg-white bg-opacity-20 p-3 rounded-lg">
              <span className="text-3xl">🐾</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold">Pet Shop</h1>
              <p className="text-pink-100 mt-1">Gestão completa do seu Pet Shop</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-pink-100 text-sm">Total de Produtos</p>
            <p className="text-3xl font-bold">{products.length}</p>
          </div>
        </div>

        {/* Sub-navegação */}
        <div className="mt-6 flex space-x-2 bg-white bg-opacity-10 rounded-lg p-1">
          {subNavItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveSubView(item.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-md transition-all ${
                activeSubView === item.id
                  ? 'bg-white text-purple-600 shadow-md'
                  : 'text-pink-100 hover:bg-white hover:bg-opacity-20'
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Area baseado na sub-view selecionada */}
      {activeSubView === 'dashboard' && (
        <PetShopDashboard statistics={statistics} products={products} loading={loading} />
      )}

      {activeSubView === 'products' && (
        <PetShopProducts 
          products={products} 
          loading={loading}
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          categoryFilter={categoryFilter}
          setCategoryFilter={setCategoryFilter}
          supplierFilter={supplierFilter}
          setSupplierFilter={setSupplierFilter}
          onCreateProduct={() => {
            setEditingProduct(null);
            setShowProductModal(true);
          }}
          onEditProduct={(product) => {
            setEditingProduct(product);
            setShowProductModal(true);
          }}
          onDeleteProduct={handleDeleteProduct}
          onStockMovement={(product) => {
            setStockProduct(product);
            setShowStockModal(true);
          }}
          onRefresh={loadPetShopData}
        />
      )}

      {activeSubView === 'sales' && (
        <PetShopSales 
          sales={sales} 
          products={products}
          loading={loading}
          onCreateSale={() => setShowSaleModal(true)}
          onRefresh={loadPetShopData}
          onShowReceipt={(receipt) => {
            setCurrentReceipt(receipt);
            setShowReceiptModal(true);
          }}
        />
      )}

      {activeSubView === 'stock-alert' && (
        <PetShopStockAlert 
          products={products} 
          loading={loading}
          onRefresh={loadPetShopData}
        />
      )}

      {/* Modal de Produto */}
      {showProductModal && (
        <PetShopProductModal
          product={editingProduct}
          onClose={() => {
            setShowProductModal(false);
            setEditingProduct(null);
          }}
          onCreate={handleCreateProduct}
          onUpdate={handleUpdateProduct}
        />
      )}

      {/* Modal de Movimentação de Estoque */}
      {showStockModal && (
        <PetShopStockModal
          product={stockProduct}
          onClose={() => {
            setShowStockModal(false);
            setStockProduct(null);
          }}
          onMovement={handleStockMovement}
        />
      )}

      {/* Modal de Comprovante */}
      {showReceiptModal && (
        <PetShopReceiptModal
          receipt={currentReceipt}
          onClose={() => {
            setShowReceiptModal(false);
            setCurrentReceipt(null);
          }}
        />
      )}
    </div>
  );
};

// Dashboard do Pet Shop
const PetShopDashboard = ({ statistics, products, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  const lowStockProducts = products.filter(p => p.current_quantity <= p.minimum_stock);

  return (
    <div className="space-y-6">
      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100">
              <Package className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total de Produtos</p>
              <p className="text-2xl font-bold text-gray-900">{statistics?.total_products || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100">
              <BarChart3 className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Quantidade em Estoque</p>
              <p className="text-2xl font-bold text-gray-900">{statistics?.total_quantity || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Estoque Baixo</p>
              <p className="text-2xl font-bold text-gray-900">{statistics?.low_stock_products || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Receita Total</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(statistics?.total_revenue || 0)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Produtos com Estoque Baixo */}
      {lowStockProducts.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Produtos com Estoque Baixo</h2>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {lowStockProducts.map((product) => (
                <div key={product.id} className="flex items-center justify-between p-4 border border-red-200 rounded-lg bg-red-50">
                  <div>
                    <p className="font-medium text-gray-900">{product.name}</p>
                    <p className="text-sm text-gray-600">SKU: {product.sku}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-red-600 font-medium">
                      Estoque: {product.current_quantity} / Mínimo: {product.minimum_stock}
                    </p>
                    <p className="text-xs text-gray-500">{product.category}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Componente de Produtos
const PetShopProducts = ({ 
  products, 
  loading, 
  searchTerm, 
  setSearchTerm, 
  categoryFilter, 
  setCategoryFilter, 
  supplierFilter, 
  setSupplierFilter,
  onCreateProduct, 
  onEditProduct, 
  onDeleteProduct,
  onStockMovement,
  onRefresh 
}) => {
  // Filtrar produtos
  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.sku.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !categoryFilter || product.category === categoryFilter;
    const matchesSupplier = !supplierFilter || product.supplier === supplierFilter;
    
    return matchesSearch && matchesCategory && matchesSupplier;
  });

  // Obter categorias e fornecedores únicos
  const categories = [...new Set(products.map(p => p.category))].filter(Boolean);
  const suppliers = [...new Set(products.map(p => p.supplier))].filter(Boolean);

  // Função para obter classe de status do estoque
  const getStockStatusClass = (product) => {
    if (product.current_quantity <= 0) {
      return 'bg-red-100 text-red-800';
    } else if (product.current_quantity <= product.minimum_stock) {
      return 'bg-red-100 text-red-800';
    } else if (product.current_quantity <= product.minimum_stock * 2) {
      return 'bg-yellow-100 text-yellow-800';
    } else {
      return 'bg-green-100 text-green-800';
    }
  };

  // Função para obter texto de status do estoque
  const getStockStatusText = (product) => {
    if (product.current_quantity <= 0) {
      return 'Sem Estoque';
    } else if (product.current_quantity <= product.minimum_stock) {
      return 'Estoque Baixo';
    } else if (product.current_quantity <= product.minimum_stock * 2) {
      return 'Atenção';
    } else {
      return 'Normal';
    }
  };

  // Função para verificar se produto está vencido ou próximo do vencimento
  const checkExpiration = (expirationDate) => {
    if (!expirationDate) return null;
    
    const expDate = new Date(expirationDate);
    const today = new Date();
    const diffTime = expDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return { status: 'expired', text: 'Vencido', class: 'bg-red-100 text-red-800' };
    if (diffDays <= 7) return { status: 'expiring', text: `${diffDays}d p/ vencer`, class: 'bg-yellow-100 text-yellow-800' };
    if (diffDays <= 30) return { status: 'warning', text: `${diffDays}d p/ vencer`, class: 'bg-blue-100 text-blue-800' };
    
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        <span className="ml-3 text-gray-600">Carregando produtos...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Gerenciar Produtos</h2>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">
              {filteredProducts.length} de {products.length} produtos
            </span>
            <button
              onClick={onCreateProduct}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors flex items-center gap-2"
            >
              <Plus size={16} />
              Novo Produto
            </button>
          </div>
        </div>

        {/* Filtros Aprimorados */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar por nome ou SKU..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">Todas as categorias</option>
            {categories.map(category => (
              <option key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </option>
            ))}
          </select>

          <select
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
            value={supplierFilter}
            onChange={(e) => setSupplierFilter(e.target.value)}
          >
            <option value="">Todos os fornecedores</option>
            {suppliers.map(supplier => (
              <option key={supplier} value={supplier}>{supplier}</option>
            ))}
          </select>

          <button
            onClick={onRefresh}
            className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-2 justify-center"
            title="Atualizar lista"
          >
            <Clock size={16} />
            Atualizar
          </button>

          <button
            onClick={() => {
              setSearchTerm('');
              setCategoryFilter('');
              setSupplierFilter('');
            }}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 justify-center"
          >
            <Filter size={16} />
            Limpar Filtros
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Produto</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categoria</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Preço Venda</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Estoque</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Validade</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredProducts.map((product) => {
              const expiration = checkExpiration(product.expiration_date);
              
              return (
                <tr key={product.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{product.name}</div>
                      {product.supplier && (
                        <div className="text-sm text-gray-500">{product.supplier}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">
                      {product.sku}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-500 capitalize">
                      {product.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {formatCurrency(product.sale_price)}
                    </div>
                    {product.cost_price > 0 && (
                      <div className="text-xs text-gray-500">
                        Custo: {formatCurrency(product.cost_price)}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex flex-col items-end">
                      <span className={`text-sm font-medium ${
                        product.current_quantity <= product.minimum_stock 
                          ? 'text-red-600' 
                          : 'text-gray-900'
                      }`}>
                        {product.current_quantity} un.
                      </span>
                      <span className="text-xs text-gray-500">
                        Mín: {product.minimum_stock}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {product.expiration_date ? (
                      <div>
                        <div className="text-sm text-gray-900">
                          {formatDate(product.expiration_date)}
                        </div>
                        {expiration && (
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${expiration.class}`}>
                            {expiration.text}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">Sem validade</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStockStatusClass(product)}`}>
                      {getStockStatusText(product)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div className="flex justify-center space-x-2">
                      <button
                        onClick={() => onEditProduct(product)}
                        className="text-purple-600 hover:text-purple-900 p-1 rounded transition-colors"
                        title="Editar produto"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => onStockMovement(product)}
                        className="text-blue-600 hover:text-blue-900 p-1 rounded transition-colors"
                        title="Movimentar estoque"
                      >
                        <Package size={16} />
                      </button>
                      <button
                        onClick={() => onDeleteProduct(product.id, product.name)}
                        className="text-red-600 hover:text-red-900 p-1 rounded transition-colors"
                        title="Excluir produto"
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

      {filteredProducts.length === 0 && (
        <div className="text-center py-12">
          {products.length === 0 ? (
            <>
              <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Nenhum produto cadastrado</p>
              <button
                onClick={onCreateProduct}
                className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors"
              >
                Adicionar primeiro produto
              </button>
            </>
          ) : (
            <>
              <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Nenhum produto encontrado com os filtros aplicados</p>
              <button
                onClick={() => {
                  setSearchTerm('');
                  setCategoryFilter('');
                  setSupplierFilter('');
                }}
                className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Limpar filtros
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

// Placeholder para os outros componentes (implementaremos nas próximas fases)
// Placeholder para os outros componentes (implementaremos nas próximas fases)
const PetShopSales = ({ sales, products, loading, onCreateSale, onRefresh, onShowReceipt }) => {
  const [searchProduct, setSearchProduct] = useState('');
  const [cart, setCart] = useState([]);
  const [customer, setCustomer] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('pix');
  const [discount, setDiscount] = useState(0);
  const [notes, setNotes] = useState('');
  const [processingSale, setProcessingSale] = useState(false);
  const [showProductSearch, setShowProductSearch] = useState(false);

  // Filtrar produtos para busca
  const filteredProducts = products.filter(product =>
    product.current_quantity > 0 &&
    (product.name.toLowerCase().includes(searchProduct.toLowerCase()) ||
     product.sku.toLowerCase().includes(searchProduct.toLowerCase()))
  ).slice(0, 5); // Mostrar máximo 5 produtos

  // Adicionar produto ao carrinho
  const addToCart = (product, quantity = 1) => {
    const existingItem = cart.find(item => item.product.id === product.id);
    
    if (existingItem) {
      if (existingItem.quantity + quantity > product.current_quantity) {
        toast.error(`Estoque insuficiente! Disponível: ${product.current_quantity}`);
        return;
      }
      
      setCart(cart.map(item =>
        item.product.id === product.id
          ? { ...item, quantity: item.quantity + quantity }
          : item
      ));
    } else {
      if (quantity > product.current_quantity) {
        toast.error(`Estoque insuficiente! Disponível: ${product.current_quantity}`);
        return;
      }
      
      setCart([...cart, { product, quantity, unitPrice: product.sale_price }]);
    }

    setSearchProduct('');
    setShowProductSearch(false);
    toast.success(`${product.name} adicionado ao carrinho!`);
  };

  // Remover produto do carrinho
  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product.id !== productId));
  };

  // Atualizar quantidade no carrinho
  const updateCartQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }

    const product = products.find(p => p.id === productId);
    if (newQuantity > product.current_quantity) {
      toast.error(`Estoque insuficiente! Disponível: ${product.current_quantity}`);
      return;
    }

    setCart(cart.map(item =>
      item.product.id === productId
        ? { ...item, quantity: newQuantity }
        : item
    ));
  };

  // Cálculos da venda
  const subtotal = cart.reduce((acc, item) => acc + (item.quantity * item.unitPrice), 0);
  const discountAmount = (subtotal * discount) / 100;
  const total = subtotal - discountAmount;

  // Processar venda
  const handleCompleteSale = async () => {
    if (cart.length === 0) {
      toast.error('Adicione produtos ao carrinho antes de finalizar a venda');
      return;
    }

    setProcessingSale(true);

    try {
      const saleData = {
        customer: customer.trim() || 'Cliente não informado',
        payment_method: paymentMethod,
        discount: discount,
        notes: notes.trim(),
        items: cart.map(item => ({
          product_id: item.product.id,
          quantity: item.quantity,
          unit_price: item.unitPrice
        }))
      };

      const response = await axios.post(`${API}/petshop/sales`, saleData);
      
      toast.success('Venda realizada com sucesso! 🎉');
      
      // Preparar dados do comprovante
      const receiptData = {
        id: response.data?.id || Date.now(),
        receipt_number: `VD${String(response.data?.id || Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
        customer: customer.trim() || 'Cliente não informado',
        payment_method: paymentMethod,
        subtotal: subtotal,
        discount: discount,
        total: total,
        notes: notes.trim(),
        items: cart.map(item => ({
          product: item.product,
          quantity: item.quantity,
          unit_price: item.unitPrice
        })),
        created_at: new Date().toISOString()
      };
      
      // Mostrar comprovante
      onShowReceipt(receiptData);
      
      // Limpar carrinho e formulário
      setCart([]);
      setCustomer('');
      setDiscount(0);
      setNotes('');
      setSearchProduct('');
      
      // Recarregar dados
      await onRefresh();
      
    } catch (error) {
      console.error('Erro ao processar venda:', error);
      if (error.response?.data?.detail?.includes('estoque')) {
        toast.error('Estoque insuficiente para alguns produtos');
      } else {
        toast.error(error.response?.data?.detail || 'Erro ao processar venda');
      }
    } finally {
      setProcessingSale(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        <span className="ml-3 text-gray-600">Carregando sistema de vendas...</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Coluna da Esquerda - Busca de Produtos */}
      <div className="lg:col-span-2 space-y-6">
        {/* Busca de Produtos */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Search className="w-5 h-5 text-green-600" />
            Buscar Produtos
          </h3>
          
          <div className="relative">
            <input
              type="text"
              placeholder="Digite o nome do produto ou SKU..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all"
              value={searchProduct}
              onChange={(e) => {
                setSearchProduct(e.target.value);
                setShowProductSearch(true);
              }}
              onFocus={() => setShowProductSearch(true)}
            />
            
            {/* Dropdown de produtos */}
            {showProductSearch && searchProduct && filteredProducts.length > 0 && (
              <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto">
                {filteredProducts.map((product) => (
                  <div
                    key={product.id}
                    onClick={() => addToCart(product)}
                    className="p-4 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-0"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900">{product.name}</p>
                        <p className="text-sm text-gray-600">
                          SKU: {product.sku} | {product.category}
                        </p>
                        <p className="text-sm text-green-600">
                          Estoque: {product.current_quantity} unidades
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-green-600">
                          {formatCurrency(product.sale_price)}
                        </p>
                        <button className="text-sm bg-green-100 text-green-700 px-2 py-1 rounded mt-1">
                          Adicionar
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {showProductSearch && searchProduct && filteredProducts.length === 0 && (
              <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg mt-1 p-4 text-center text-gray-500">
                Nenhum produto encontrado
              </div>
            )}
          </div>
        </div>

        {/* Lista do Carrinho */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-green-600" />
            Carrinho de Compras ({cart.length} itens)
          </h3>

          {cart.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <ShoppingCart className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Carrinho vazio</p>
              <p className="text-sm">Busque produtos acima para adicionar ao carrinho</p>
            </div>
          ) : (
            <div className="space-y-3">
              {cart.map((item) => (
                <div key={item.product.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.product.name}</p>
                    <p className="text-sm text-gray-600">
                      SKU: {item.product.sku} | {formatCurrency(item.unitPrice)} cada
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateCartQuantity(item.product.id, item.quantity - 1)}
                        className="w-8 h-8 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded-full"
                      >
                        -
                      </button>
                      <span className="w-12 text-center font-medium">{item.quantity}</span>
                      <button
                        onClick={() => updateCartQuantity(item.product.id, item.quantity + 1)}
                        className="w-8 h-8 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded-full"
                      >
                        +
                      </button>
                    </div>
                    
                    <div className="text-right min-w-[80px]">
                      <p className="font-bold text-green-600">
                        {formatCurrency(item.quantity * item.unitPrice)}
                      </p>
                    </div>
                    
                    <button
                      onClick={() => removeFromCart(item.product.id)}
                      className="text-red-500 hover:text-red-700 p-1"
                      title="Remover item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Coluna da Direita - Resumo da Venda */}
      <div className="space-y-6">
        {/* Resumo da Venda */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            Resumo da Venda
          </h3>

          <div className="space-y-4">
            {/* Subtotal */}
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal:</span>
              <span className="font-medium">{formatCurrency(subtotal)}</span>
            </div>

            {/* Campo de desconto */}
            <div>
              <label className="block text-sm text-gray-600 mb-2">
                Desconto (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all"
                value={discount}
                onChange={(e) => setDiscount(Math.max(0, Math.min(100, parseFloat(e.target.value) || 0)))}
                placeholder="0"
              />
            </div>

            {/* Desconto aplicado */}
            {discount > 0 && (
              <div className="flex justify-between text-red-600">
                <span>Desconto ({discount}%):</span>
                <span>-{formatCurrency(discountAmount)}</span>
              </div>
            )}

            {/* Total */}
            <div className="flex justify-between text-lg font-bold border-t pt-3">
              <span>Total:</span>
              <span className="text-green-600">{formatCurrency(total)}</span>
            </div>

            {/* Forma de pagamento */}
            <div>
              <label className="block text-sm text-gray-600 mb-2">
                Forma de Pagamento
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all"
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
              >
                <option value="pix">PIX</option>
                <option value="dinheiro">Dinheiro</option>
                <option value="cartao_debito">Cartão de Débito</option>
                <option value="cartao_credito">Cartão de Crédito</option>
              </select>
            </div>

            {/* Cliente */}
            <div>
              <label className="block text-sm text-gray-600 mb-2">
                Cliente (opcional)
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all"
                value={customer}
                onChange={(e) => setCustomer(e.target.value)}
                placeholder="Nome do cliente"
              />
            </div>

            {/* Observações */}
            <div>
              <label className="block text-sm text-gray-600 mb-2">
                Observações
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-200 transition-all"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Observações sobre a venda..."
                rows="2"
              />
            </div>

            {/* Botão de finalizar venda */}
            <button
              onClick={handleCompleteSale}
              disabled={cart.length === 0 || processingSale}
              className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {processingSale ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Processando...
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  Finalizar Venda
                </>
              )}
            </button>
          </div>
        </div>

        {/* Histórico de Vendas Recentes */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-green-600" />
            Vendas Recentes
          </h3>

          {sales.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Nenhuma venda realizada ainda</p>
          ) : (
            <div className="space-y-3">
              {sales.slice(0, 5).map((sale) => (
                <div key={sale.id} className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                     onClick={() => {
                       const receiptData = {
                         id: sale.id,
                         receipt_number: `VD${String(sale.id).padStart(4, '0')}`,
                         customer: sale.customer || 'Cliente não informado',
                         payment_method: sale.payment_method,
                         subtotal: sale.subtotal || sale.total,
                         discount: sale.discount || 0,
                         total: sale.total,
                         notes: sale.notes || '',
                         items: sale.items || [],
                         created_at: sale.created_at
                       };
                       onShowReceipt(receiptData);
                     }}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {sale.customer || 'Cliente não informado'}
                      </p>
                      <p className="text-xs text-gray-600">
                        {new Date(sale.created_at).toLocaleDateString('pt-BR')} às {' '}
                        {new Date(sale.created_at).toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                      <p className="text-xs text-gray-500 capitalize">
                        {sale.payment_method.replace('_', ' ')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-green-600">
                        {formatCurrency(sale.total)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {sale.items?.length || 0} itens
                      </p>
                      <p className="text-xs text-blue-600 hover:text-blue-800 mt-1">
                        Ver comprovante →
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const PetShopStockAlert = ({ products, loading, onRefresh }) => {
  // Filtrar produtos com estoque baixo
  const lowStockProducts = products.filter(product => 
    product.current_quantity <= product.minimum_stock
  );

  // Filtrar produtos sem estoque
  const outOfStockProducts = products.filter(product => 
    product.current_quantity <= 0
  );

  // Filtrar produtos próximos do vencimento (30 dias)
  const expiringProducts = products.filter(product => {
    if (!product.expiration_date) return false;
    
    const expDate = new Date(product.expiration_date);
    const today = new Date();
    const diffTime = expDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays <= 30 && diffDays >= 0;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
        <span className="ml-3 text-gray-600">Carregando alertas...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header com Resumo */}
      <div className="bg-gradient-to-r from-red-500 to-orange-500 rounded-xl shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="bg-white bg-opacity-20 p-3 rounded-lg">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">Alertas de Estoque</h2>
              <p className="text-red-100 mt-1">Produtos que requerem atenção</p>
            </div>
          </div>
          <div className="text-right">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-red-100">Sem Estoque</p>
                <p className="text-2xl font-bold">{outOfStockProducts.length}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-red-100">Estoque Baixo</p>
                <p className="text-2xl font-bold">{lowStockProducts.length}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-red-100">Vencendo</p>
                <p className="text-2xl font-bold">{expiringProducts.length}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Produtos Sem Estoque */}
      {outOfStockProducts.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-red-600 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                🚨 Produtos Sem Estoque ({outOfStockProducts.length})
              </h3>
              <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium">
                CRÍTICO
              </span>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {outOfStockProducts.map((product) => (
                <div key={product.id} className="flex items-center justify-between p-4 border-2 border-red-200 rounded-lg bg-red-50">
                  <div>
                    <p className="font-semibold text-gray-900">{product.name}</p>
                    <p className="text-sm text-gray-600">SKU: {product.sku}</p>
                    <p className="text-sm text-gray-600 capitalize">{product.category}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-red-600">0</p>
                    <p className="text-xs text-gray-500">unidades</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Produtos com Estoque Baixo */}
      {lowStockProducts.filter(p => p.current_quantity > 0).length > 0 && (
        <div className="bg-white rounded-xl shadow-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-orange-600 flex items-center gap-2">
                <Package className="w-5 h-5" />
                ⚠️ Estoque Baixo ({lowStockProducts.filter(p => p.current_quantity > 0).length})
              </h3>
              <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm font-medium">
                ATENÇÃO
              </span>
            </div>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-500">Produto</th>
                    <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Estoque Atual</th>
                    <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Estoque Mínimo</th>
                    <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Diferença</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {lowStockProducts.filter(p => p.current_quantity > 0).map((product) => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium text-gray-900">{product.name}</p>
                          <p className="text-sm text-gray-500">SKU: {product.sku}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-lg font-bold text-orange-600">
                          {product.current_quantity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-gray-700">{product.minimum_stock}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-red-600 font-medium">
                          -{(product.minimum_stock - product.current_quantity)} un.
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Produtos Próximos do Vencimento */}
      {expiringProducts.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-yellow-600 flex items-center gap-2">
                <Clock className="w-5 h-5" />
                🕒 Produtos Próximos do Vencimento ({expiringProducts.length})
              </h3>
              <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-medium">
                ATENÇÃO
              </span>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {expiringProducts
                .sort((a, b) => new Date(a.expiration_date) - new Date(b.expiration_date))
                .map((product) => {
                  const expDate = new Date(product.expiration_date);
                  const today = new Date();
                  const diffTime = expDate - today;
                  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                  
                  return (
                    <div key={product.id} className="flex items-center justify-between p-4 border border-yellow-200 rounded-lg bg-yellow-50">
                      <div>
                        <p className="font-semibold text-gray-900">{product.name}</p>
                        <p className="text-sm text-gray-600">SKU: {product.sku}</p>
                        <p className="text-sm text-gray-600">Estoque: {product.current_quantity} unidades</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Vence em:</p>
                        <p className={`text-lg font-bold ${
                          diffDays <= 7 ? 'text-red-600' : 'text-yellow-600'
                        }`}>
                          {diffDays} dias
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(product.expiration_date)}
                        </p>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      )}

      {/* Estado sem alertas */}
      {lowStockProducts.length === 0 && expiringProducts.length === 0 && (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">✅ Tudo em Ordem!</h3>
          <p className="text-gray-600 mb-4">
            Não há produtos com estoque baixo ou próximos do vencimento no momento.
          </p>
          <button
            onClick={onRefresh}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 mx-auto"
          >
            <Clock size={16} />
            Atualizar Lista
          </button>
        </div>
      )}
    </div>
  );
};

// 🐾 Pet Shop Product Modal Component
const PetShopProductModal = ({ product, onClose, onCreate, onUpdate }) => {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    category: 'ração',
    supplier: '',
    current_quantity: '',
    cost_price: '',
    sale_price: '',
    expiration_date: '',
    minimum_stock: '',
    description: ''
  });

  const [loading, setLoading] = useState(false);

  // Categorias do Pet Shop
  const petCategories = [
    'ração', 'petisco', 'higiene', 'brinquedos', 'acessórios', 
    'medicamentos', 'camas', 'coleiras', 'comedouros', 'outros'
  ];

  // Preencher formulário se editando produto
  React.useEffect(() => {
    if (product) {
      setFormData({
        name: product.name || '',
        sku: product.sku || '',
        category: product.category || 'ração',
        supplier: product.supplier || '',
        current_quantity: product.current_quantity?.toString() || '',
        cost_price: product.cost_price?.toString() || '',
        sale_price: product.sale_price?.toString() || '',
        expiration_date: product.expiration_date ? new Date(product.expiration_date).toISOString().split('T')[0] : '',
        minimum_stock: product.minimum_stock?.toString() || '',
        description: product.description || ''
      });
    }
  }, [product]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Validações
      if (!formData.name.trim()) {
        toast.error('Nome do produto é obrigatório');
        return;
      }

      if (!formData.sku.trim()) {
        toast.error('SKU é obrigatório');
        return;
      }

      if (!formData.sale_price || parseFloat(formData.sale_price) <= 0) {
        toast.error('Preço de venda deve ser maior que zero');
        return;
      }

      const productData = {
        name: formData.name.trim(),
        sku: formData.sku.trim().toUpperCase(),
        category: formData.category,
        supplier: formData.supplier.trim(),
        current_quantity: parseInt(formData.current_quantity) || 0,
        cost_price: parseFloat(formData.cost_price) || 0,
        sale_price: parseFloat(formData.sale_price),
        expiration_date: formData.expiration_date ? new Date(formData.expiration_date).toISOString() : null,
        minimum_stock: parseInt(formData.minimum_stock) || 0,
        description: formData.description.trim()
      };

      if (product) {
        await onUpdate(product.id, productData);
      } else {
        await onCreate(productData);
      }
    } catch (error) {
      console.error('Erro no formulário:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[95vh] overflow-y-auto">
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 rounded-t-xl">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Package className="w-6 h-6 text-purple-600" />
              {product ? 'Editar Produto' : 'Novo Produto'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Nome e SKU */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome do Produto *
              </label>
              <input
                type="text"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Ex: Ração Premium para Cães"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SKU (Código Único) *
              </label>
              <input
                type="text"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.sku}
                onChange={(e) => setFormData({...formData, sku: e.target.value.toUpperCase()})}
                placeholder="Ex: RAC001"
                style={{ textTransform: 'uppercase' }}
              />
            </div>
          </div>

          {/* Categoria e Fornecedor */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Categoria *
              </label>
              <select
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
              >
                {petCategories.map(category => (
                  <option key={category} value={category}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fornecedor
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.supplier}
                onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                placeholder="Nome do fornecedor"
              />
            </div>
          </div>

          {/* Quantidade e Estoque Mínimo */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quantidade Atual
              </label>
              <input
                type="number"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.current_quantity}
                onChange={(e) => setFormData({...formData, current_quantity: e.target.value})}
                placeholder="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estoque Mínimo
              </label>
              <input
                type="number"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.minimum_stock}
                onChange={(e) => setFormData({...formData, minimum_stock: e.target.value})}
                placeholder="5"
              />
              <p className="text-xs text-gray-500 mt-1">
                Alerta quando estoque atingir este valor
              </p>
            </div>
          </div>

          {/* Preços */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preço de Custo (R$)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.cost_price}
                onChange={(e) => setFormData({...formData, cost_price: e.target.value})}
                placeholder="0,00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preço de Venda (R$) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.sale_price}
                onChange={(e) => setFormData({...formData, sale_price: e.target.value})}
                placeholder="0,00"
              />
            </div>
          </div>

          {/* Data de Validade */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data de Validade (se aplicável)
              </label>
              <input
                type="date"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                value={formData.expiration_date}
                onChange={(e) => setFormData({...formData, expiration_date: e.target.value})}
              />
              <p className="text-xs text-gray-500 mt-1">
                Deixe em branco se não tem validade
              </p>
            </div>

            {/* Margem de Lucro (calculada) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Margem de Lucro
              </label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                <span className="text-sm text-gray-700">
                  {formData.cost_price && formData.sale_price 
                    ? `${(((parseFloat(formData.sale_price) - parseFloat(formData.cost_price)) / parseFloat(formData.sale_price)) * 100).toFixed(1)}%`
                    : 'Digite os preços para calcular'
                  }
                </span>
              </div>
            </div>
          </div>

          {/* Descrição */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Descrição do Produto
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Descrição detalhada do produto..."
              rows="3"
            />
          </div>

          {/* Botões de Ação */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Salvando...
                </>
              ) : (
                <>
                  {product ? 'Atualizar' : 'Criar'} Produto
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// 🐾 Pet Shop Stock Movement Modal Component
const PetShopStockModal = ({ product, onClose, onMovement }) => {
  const [formData, setFormData] = useState({
    type: 'entrada',
    quantity: '',
    reason: '',
    notes: ''
  });

  const [loading, setLoading] = useState(false);

  // Razões pré-definidas para movimentação
  const entryReasons = [
    'Compra', 'Devolução de cliente', 'Ajuste de inventário', 
    'Transferência', 'Promoção', 'Outros'
  ];

  const exitReasons = [
    'Venda', 'Avaria', 'Vencimento', 'Perda', 
    'Transferência', 'Amostra', 'Outros'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Validações
      if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
        toast.error('Quantidade deve ser maior que zero');
        return;
      }

      if (!formData.reason) {
        toast.error('Selecione um motivo para a movimentação');
        return;
      }

      // Validação para saída (não pode ser maior que estoque atual)
      if (formData.type === 'saida' && parseFloat(formData.quantity) > product.current_quantity) {
        toast.error(`Quantidade não pode ser maior que o estoque atual (${product.current_quantity})`);
        return;
      }

      const movementData = {
        product_id: product.id,
        type: formData.type,
        quantity: parseInt(formData.quantity),
        reason: formData.reason,
        notes: formData.notes.trim()
      };

      await onMovement(movementData);
    } catch (error) {
      console.error('Erro no formulário de movimentação:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!product) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[95vh] overflow-y-auto">
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 rounded-t-xl">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Package className="w-6 h-6 text-blue-600" />
              Movimentar Estoque
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Informações do Produto */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">{product.name}</h3>
                <p className="text-sm text-gray-600">SKU: {product.sku}</p>
                <p className="text-sm text-gray-600 capitalize">Categoria: {product.category}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Estoque Atual</p>
                <p className={`text-2xl font-bold ${
                  product.current_quantity <= product.minimum_stock ? 'text-red-600' : 'text-gray-900'
                }`}>
                  {product.current_quantity} un.
                </p>
                <p className="text-xs text-gray-500">Mín: {product.minimum_stock}</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Tipo de Movimentação */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Tipo de Movimentação *
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setFormData({...formData, type: 'entrada', reason: ''})}
                  className={`p-4 rounded-lg border-2 transition-all text-center ${
                    formData.type === 'entrada'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 hover:border-green-300'
                  }`}
                >
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Plus className="w-5 h-5" />
                    <span className="font-medium">ENTRADA</span>
                  </div>
                  <p className="text-sm">Adicionar produtos ao estoque</p>
                </button>

                <button
                  type="button"
                  onClick={() => setFormData({...formData, type: 'saida', reason: ''})}
                  className={`p-4 rounded-lg border-2 transition-all text-center ${
                    formData.type === 'saida'
                      ? 'border-red-500 bg-red-50 text-red-700'
                      : 'border-gray-200 hover:border-red-300'
                  }`}
                >
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Trash2 className="w-5 h-5" />
                    <span className="font-medium">SAÍDA</span>
                  </div>
                  <p className="text-sm">Remover produtos do estoque</p>
                </button>
              </div>
            </div>

            {/* Quantidade e Motivo */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quantidade *
                </label>
                <input
                  type="number"
                  min="1"
                  max={formData.type === 'saida' ? product.current_quantity : undefined}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  value={formData.quantity}
                  onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                  placeholder="Digite a quantidade"
                />
                {formData.type === 'saida' && (
                  <p className="text-xs text-gray-500 mt-1">
                    Máximo disponível: {product.current_quantity} unidades
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Motivo *
                </label>
                <select
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  value={formData.reason}
                  onChange={(e) => setFormData({...formData, reason: e.target.value})}
                >
                  <option value="">Selecione o motivo</option>
                  {(formData.type === 'entrada' ? entryReasons : exitReasons).map(reason => (
                    <option key={reason} value={reason}>{reason}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Prévia do Novo Estoque */}
            {formData.quantity && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Prévia da Movimentação:</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Estoque Atual</p>
                    <p className="font-semibold">{product.current_quantity} un.</p>
                  </div>
                  <div>
                    <p className="text-gray-500">
                      {formData.type === 'entrada' ? 'Entrada' : 'Saída'}
                    </p>
                    <p className={`font-semibold ${formData.type === 'entrada' ? 'text-green-600' : 'text-red-600'}`}>
                      {formData.type === 'entrada' ? '+' : '-'}{formData.quantity} un.
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Novo Estoque</p>
                    <p className={`font-semibold ${
                      (formData.type === 'entrada' 
                        ? product.current_quantity + parseInt(formData.quantity || 0)
                        : product.current_quantity - parseInt(formData.quantity || 0)
                      ) <= product.minimum_stock ? 'text-red-600' : 'text-gray-900'
                    }`}>
                      {formData.type === 'entrada' 
                        ? product.current_quantity + parseInt(formData.quantity || 0)
                        : product.current_quantity - parseInt(formData.quantity || 0)
                      } un.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Observações */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Observações
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                placeholder="Observações adicionais sobre a movimentação..."
                rows="3"
              />
            </div>

            {/* Botões de Ação */}
            <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className={`px-6 py-2 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 ${
                  formData.type === 'entrada'
                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700'
                    : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700'
                }`}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Processando...
                  </>
                ) : (
                  <>
                    {formData.type === 'entrada' ? 'Confirmar Entrada' : 'Confirmar Saída'}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// 🧾 Pet Shop Receipt Modal Component
const PetShopReceiptModal = ({ receipt, onClose }) => {
  if (!receipt) return null;

  const receiptDate = new Date(receipt.created_at || Date.now());
  const receiptNumber = receipt.receipt_number || `VD${String(receipt.id || Math.floor(Math.random() * 10000)).padStart(4, '0')}`;

  const handlePrint = () => {
    const printContent = document.getElementById('receipt-content');
    const originalContent = document.body.innerHTML;
    
    document.body.innerHTML = printContent.innerHTML;
    window.print();
    document.body.innerHTML = originalContent;
    window.location.reload();
  };

  const handleDownload = () => {
    const element = document.getElementById('receipt-content');
    const receiptText = `
COMPROVANTE DE VENDA - PETSHOP
==========================================
Número: ${receiptNumber}
Data: ${receiptDate.toLocaleDateString('pt-BR')} às ${receiptDate.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}
Cliente: ${receipt.customer || 'Cliente não informado'}
Forma de Pagamento: ${receipt.payment_method?.replace('_', ' ').toUpperCase() || 'PIX'}

PRODUTOS:
------------------------------------------
${receipt.items?.map(item => 
  `${item.product?.name || 'Produto'} - ${item.quantity}x ${formatCurrency(item.unit_price)} = ${formatCurrency(item.quantity * item.unit_price)}`
).join('\n') || ''}

------------------------------------------
Subtotal: ${formatCurrency(receipt.subtotal || 0)}
Desconto (${receipt.discount || 0}%): -${formatCurrency(((receipt.subtotal || 0) * (receipt.discount || 0)) / 100)}
TOTAL: ${formatCurrency(receipt.total || 0)}

${receipt.notes ? `Observações: ${receipt.notes}` : ''}

Obrigado pela preferência!
OrçaZen Pet Shop
==========================================
    `.trim();

    const blob = new Blob([receiptText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Comprovante_${receiptNumber}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[95vh] overflow-y-auto">
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-gray-200 rounded-t-xl">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <FileText className="w-6 h-6 text-green-600" />
              Comprovante de Venda
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <div id="receipt-content" className="p-8">
          {/* Header do Comprovante */}
          <div className="text-center border-b-2 border-gray-200 pb-6 mb-6">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 rounded-lg mb-4">
              <h1 className="text-2xl font-bold">🐾 OrçaZen Pet Shop</h1>
              <p className="text-purple-100">Tudo para seu melhor amigo</p>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="text-left">
                <p className="font-semibold text-gray-900">Comprovante: #{receiptNumber}</p>
                <p className="text-gray-600">
                  {receiptDate.toLocaleDateString('pt-BR')} às {receiptDate.toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-gray-900">Cliente:</p>
                <p className="text-gray-600">{receipt.customer || 'Cliente não informado'}</p>
                <p className="text-xs text-gray-500 mt-1 capitalize">
                  Pagamento: {receipt.payment_method?.replace('_', ' ') || 'PIX'}
                </p>
              </div>
            </div>
          </div>

          {/* Lista de Produtos */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Produtos Vendidos</h3>
            <div className="space-y-3">
              {receipt.items?.map((item, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.product?.name || 'Produto'}</p>
                    <p className="text-sm text-gray-600">
                      SKU: {item.product?.sku || 'N/A'} | {item.product?.category || 'Categoria'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">
                      {item.quantity}x {formatCurrency(item.unit_price)}
                    </p>
                    <p className="font-bold text-green-600">
                      {formatCurrency(item.quantity * item.unit_price)}
                    </p>
                  </div>
                </div>
              )) || []}
            </div>
          </div>

          {/* Totais */}
          <div className="border-t-2 border-gray-200 pt-4 mb-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal:</span>
                <span className="font-medium">{formatCurrency(receipt.subtotal || 0)}</span>
              </div>
              
              {receipt.discount > 0 && (
                <div className="flex justify-between text-red-600">
                  <span>Desconto ({receipt.discount}%):</span>
                  <span>-{formatCurrency(((receipt.subtotal || 0) * receipt.discount) / 100)}</span>
                </div>
              )}
              
              <div className="flex justify-between text-xl font-bold border-t pt-2">
                <span>TOTAL:</span>
                <span className="text-green-600">{formatCurrency(receipt.total || 0)}</span>
              </div>
            </div>
          </div>

          {/* Observações */}
          {receipt.notes && (
            <div className="mb-6">
              <h4 className="font-semibold text-gray-900 mb-2">Observações:</h4>
              <p className="text-gray-600 bg-gray-50 p-3 rounded-lg">{receipt.notes}</p>
            </div>
          )}

          {/* Rodapé */}
          <div className="text-center border-t-2 border-gray-200 pt-4">
            <p className="text-lg font-semibold text-green-600 mb-2">✨ Obrigado pela preferência! ✨</p>
            <p className="text-sm text-gray-600">Volte sempre ao OrçaZen Pet Shop</p>
            <p className="text-xs text-gray-500 mt-2">
              Comprovante gerado em {new Date().toLocaleDateString('pt-BR')} às {new Date().toLocaleTimeString('pt-BR')}
            </p>
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="sticky bottom-0 bg-white px-6 py-4 border-t border-gray-200 rounded-b-xl">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Fechar
            </button>
            <button
              onClick={handleDownload}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Download size={16} />
              Baixar TXT
            </button>
            <button
              onClick={handlePrint}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <FileText size={16} />
              Imprimir
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// 🔍 Global Search Bar Component
const GlobalSearchBar = ({ isVisible, onToggle, searchQuery, onSearchChange, searchResults }) => {
  const searchRef = React.useRef(null);

  React.useEffect(() => {
    if (isVisible && searchRef.current) {
      searchRef.current.focus();
    }
  }, [isVisible]);

  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        onToggle();
      }
    };

    if (isVisible) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isVisible, onToggle]);

  return (
    <div className="flex-1 max-w-2xl mx-4">
      <div className="relative" ref={searchRef}>
        {!isVisible ? (
          <button
            onClick={onToggle}
            className="w-full flex items-center px-4 py-2 text-gray-500 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Search className="w-5 h-5 mr-3" />
            <span>Buscar produtos, clientes, módulos...</span>
          </button>
        ) : (
          <>
            <div className="flex items-center bg-white border-2 border-blue-500 rounded-lg shadow-lg">
              <Search className="w-5 h-5 ml-3 text-gray-400" />
              <input
                ref={searchRef}
                type="text"
                placeholder="Digite para buscar..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="w-full px-3 py-3 bg-transparent outline-none text-gray-900"
              />
              <button
                onClick={onToggle}
                className="p-2 m-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
              >
                ✕
              </button>
            </div>

            {/* Search Results Dropdown */}
            {searchResults.length > 0 && (
              <div className="absolute z-50 w-full mt-2 bg-white rounded-lg shadow-xl border max-h-96 overflow-y-auto">
                {searchResults.map((category, categoryIndex) => (
                  <div key={categoryIndex} className="p-2">
                    <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase bg-gray-50 rounded-t">
                      {category.category}
                    </div>
                    {category.items.map((item, itemIndex) => (
                      <button
                        key={itemIndex}
                        onClick={item.action}
                        className="w-full text-left px-3 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-0"
                      >
                        <div className="flex items-center">
                          {item.icon && <span className="mr-3 text-lg">{item.icon}</span>}
                          <div>
                            <div className="font-medium text-gray-900">{item.title}</div>
                            <div className="text-sm text-gray-600">{item.subtitle}</div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                ))}
                
                {searchQuery && searchResults.length === 0 && (
                  <div className="p-4 text-center text-gray-500">
                    <Search className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p>Nenhum resultado encontrado</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// 📱 Sidebar Component
const SidebarComponent = ({ collapsed, onToggle, activeView, onViewChange, onCreditCardsClick }) => {
  const [showPetShopSubmenu, setShowPetShopSubmenu] = useState(false);

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3, color: 'blue' },
    { id: 'transactions', label: 'Transações', icon: CreditCard, color: 'green' },
    { id: 'accounts', label: 'Contas', icon: PiggyBank, color: 'purple' },
    { id: 'goals', label: 'Metas', icon: Target, color: 'pink' },
    { id: 'budgets', label: 'Orçamentos', icon: TrendingUp, color: 'orange' },
    { id: 'ai', label: 'IA Financeira', icon: Settings, color: 'indigo', emoji: '🧠' },
    { id: 'consortiums', label: 'Consórcios', icon: DollarSign, color: 'emerald', emoji: '🏠' },
    { id: 'credit-cards', label: 'Cartões', icon: CreditCard, color: 'amber', emoji: '💳', action: onCreditCardsClick },
    { id: 'profile', label: 'Perfil', icon: Settings, color: 'slate', emoji: '👤' },
    { id: 'import', label: 'Importar', icon: Upload, color: 'teal', emoji: '📄' },
    { id: 'contracts', label: 'Contratos', icon: FileText, color: 'violet', emoji: '🏠' }
  ];

  const petShopSubmenu = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'products', label: 'Produtos', icon: Package },
    { id: 'sales', label: 'Vendas', icon: ShoppingCart },
    { id: 'stock-alert', label: 'Estoque Baixo', icon: AlertTriangle }
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">O</span>
              </div>
              <span className="font-bold text-gray-900">OrçaZen</span>
            </div>
          )}
          <button
            onClick={onToggle}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title={collapsed ? 'Expandir sidebar' : 'Recolher sidebar'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {collapsed ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7M19 19l-7-7 7-7" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => item.action ? item.action() : onViewChange(item.id)}
              className={`w-full flex items-center ${collapsed ? 'justify-center p-3' : 'px-3 py-3'} rounded-lg transition-all group ${
                isActive 
                  ? `bg-${item.color}-100 text-${item.color}-700 shadow-sm`
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
              title={collapsed ? item.label : undefined}
            >
              {item.emoji ? (
                <span className="text-xl">{item.emoji}</span>
              ) : (
                <Icon className={`w-5 h-5 ${collapsed ? '' : 'mr-3'}`} />
              )}
              {!collapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </button>
          );
        })}

        {/* Pet Shop com Submenu */}
        <div className="relative">
          <button
            onClick={() => {
              if (collapsed) {
                onViewChange('petshop');
              } else {
                setShowPetShopSubmenu(!showPetShopSubmenu);
              }
            }}
            className={`w-full flex items-center ${collapsed ? 'justify-center p-3' : 'px-3 py-3 justify-between'} rounded-lg transition-all group ${
              activeView === 'petshop'
                ? 'bg-pink-100 text-pink-700 shadow-sm'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
            }`}
            title={collapsed ? 'Pet Shop' : undefined}
          >
            <div className="flex items-center">
              <span className="text-xl">🐾</span>
              {!collapsed && <span className="font-medium ml-3">Pet Shop</span>}
            </div>
            {!collapsed && (
              <svg 
                className={`w-4 h-4 transition-transform ${showPetShopSubmenu ? 'rotate-180' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            )}
          </button>

          {/* Pet Shop Submenu */}
          {showPetShopSubmenu && !collapsed && (
            <div className="ml-6 mt-1 space-y-1 border-l-2 border-gray-200 pl-2">
              {petShopSubmenu.map((subItem) => {
                const SubIcon = subItem.icon;
                return (
                  <button
                    key={subItem.id}
                    onClick={() => {
                      onViewChange('petshop');
                      // Aqui você pode adicionar lógica para definir a sub-view do pet shop
                    }}
                    className="w-full flex items-center px-3 py-2 rounded-lg transition-all text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  >
                    <SubIcon className="w-4 h-4 mr-2" />
                    <span>{subItem.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </nav>

      {/* Sidebar Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            <p>OrçaZen Financeiro</p>
            <p>v1.0.0 - PWA</p>
          </div>
        </div>
      )}
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