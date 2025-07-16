"use client";

import { useAuth } from "react-oidc-context";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import useRequireAuth from "../../components/useRequireAuth";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { getClassesForDashboard, ClassData } from "../../lib/api";
import { 
  Users, 
  BookOpen, 
  Sparkles,
  GraduationCap,
  Target,
  Zap
} from "lucide-react";

const colorOptions = [
  { color: "from-amber-500 to-orange-600", bgColor: "from-amber-50 to-orange-50" },
  { color: "from-emerald-500 to-teal-600", bgColor: "from-emerald-50 to-teal-50" },
  { color: "from-blue-500 to-indigo-600", bgColor: "from-blue-50 to-indigo-50" },
  { color: "from-purple-500 to-pink-600", bgColor: "from-purple-50 to-pink-50" },
  { color: "from-rose-500 to-pink-600", bgColor: "from-rose-50 to-pink-50" },
  { color: "from-green-500 to-emerald-600", bgColor: "from-green-50 to-emerald-50" }
];

interface ClassItem extends ClassData {
  color: string;
  bgColor: string;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5
    }
  }
};

export default function DashboardPage() {
  const auth = useAuth();
  const router = useRouter();
  const [classes, setClasses] = useState<ClassItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useRequireAuth();

  useEffect(() => {
    const fetchClasses = async () => {
      if (!auth.user?.profile?.email) return;
      
      try {
        // Store teacherID (email) in localStorage for WebSocket connections
        window.localStorage.setItem('teacherID', auth.user.profile.email);
        
        setLoading(true);
        const classData = await getClassesForDashboard(auth.user.profile.email);
        
        const classesWithColors = classData.map((cls, index) => ({
          ...cls,
          ...colorOptions[index % colorOptions.length]
        }));
        
        setClasses(classesWithColors);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load classes');
      } finally {
        setLoading(false);
      }
    };

    if (auth.isAuthenticated && !auth.isLoading) {
      fetchClasses();
    }
  }, [auth.isAuthenticated, auth.isLoading, auth.user?.profile?.email]);

  if (auth.isLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
        <p className="ml-4 text-lg font-medium text-gray-700">Loading your dashboard...</p>
      </div>
    );
  }
  
  if (auth.error || error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-red-50 to-pink-50">
        <div className="text-center p-8 bg-white rounded-2xl shadow-xl border border-red-200">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Zap className="w-8 h-8 text-red-600" />
          </div>
          <p className="text-lg font-semibold text-red-800">Oops! Something went wrong</p>
          <p className="text-red-600 mt-2">{auth.error?.message || error}</p>
        </div>
      </div>
    );
  }



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-600/20 rounded-full blur-3xl animate-float" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-pink-400/20 to-orange-600/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-indigo-400/10 to-purple-600/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
      </div>

      {/* Header */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 bg-white/90 border-b border-gray-200 backdrop-blur-xl"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <motion.div
                whileHover={{ scale: 1.05, rotate: 5 }}
                className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg"
              >
                <GraduationCap className="h-8 w-8 text-white" />
              </motion.div>
              <div>
                <motion.h1 
                  className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  CoTeacher Dashboard
                </motion.h1>
                <motion.p 
                  className="text-gray-600 font-medium"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  Welcome back, <span className="text-blue-600 font-semibold">{auth.user?.profile['cognito:username'] || auth.user?.profile.email?.split('@')[0] || 'User'}</span>
                </motion.p>
              </div>
            </div>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button 
                variant="outline" 
                onClick={() => auth.removeUser()}
                className="bg-gray-800 text-white border-gray-700 hover:bg-gray-900 shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Sign Out
              </Button>
            </motion.div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">


        {/* Section Header */}
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center space-x-3 mb-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-lg">
              <Target className="h-5 w-5 text-white" />
            </div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-blue-800 bg-clip-text text-transparent">
              Your Classes
            </h2>
          </div>
          <p className="text-gray-600 font-medium"></p>
        </motion.div>

        {/* Classes Grid */}
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {classes.map((classItem, index) => (
            <motion.div
              key={classItem.classID}
              variants={itemVariants}
              whileHover={{ 
                scale: 1.02, 
                y: -5,
                transition: { duration: 0.2 }
              }}
              whileTap={{ scale: 0.98 }}
              className="group cursor-pointer"
              onClick={() => router.push(`/chat/${classItem.classID}`)}
            >
              <Card className={`relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-500 bg-gradient-to-br ${classItem.bgColor} backdrop-blur-sm`}>
                {/* Gradient border effect */}
                <div className={`absolute inset-0 bg-gradient-to-br ${classItem.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300 rounded-lg`} />
                
                {/* Shimmer effect */}
                <div className="absolute inset-0 shimmer-effect opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                
                <CardHeader className="pb-4 relative z-10">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <motion.div
                        whileHover={{ rotate: 10, scale: 1.1 }}
                        className={`p-3 bg-gradient-to-br ${classItem.color} rounded-xl shadow-lg text-white`}
                      >
                        <BookOpen className="h-5 w-5" />
                      </motion.div>
                      <div>
                        <CardTitle className="text-lg font-bold text-gray-900 group-hover:text-gray-800 transition-colors">
                          {classItem.classTitle}
                        </CardTitle>
                      </div>
                    </div>
                    <Badge variant="glow" className={`bg-gradient-to-r ${classItem.color} text-white shadow-lg`}>
                      Section {classItem.sectionNumber}
                    </Badge>
                  </div>

                </CardHeader>
                
                <CardContent className="relative z-10">
                  <div className="flex items-center space-x-2 text-gray-700">
                    <Users className="h-4 w-4" />
                    <span className="text-sm font-medium">
                      {classItem.numStudents} student{parseInt(classItem.numStudents) !== 1 ? 's' : ''}
                    </span>
                  </div>
                </CardContent>
                
                {/* Floating elements */}
                <div className={`absolute -right-6 -bottom-6 w-20 h-20 bg-gradient-to-br ${classItem.color} opacity-10 rounded-full blur-xl group-hover:opacity-20 transition-opacity duration-300`} />
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </main>
    </div>
  );
}
