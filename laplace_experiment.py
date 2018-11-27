# -*- coding: utf-8 -*-
"""
Created on Thu Aug  2 14:00:27 2018

@author: inawashiro
"""
import laplace_theory

# For Visualization
import matplotlib.pyplot as plt

# For Numerical Computation 
import numpy as np
from numpy import dot, absolute
from numpy.linalg import norm, solve, eigvals

# For Symbolic Notation
import sympy as sym
from sympy import Symbol, diff, lambdify, nsolve
sym.init_printing()

# For Displaying Symbolic Notation
from IPython.display import display

# For Random Variables
import random

# For Measuring Computation Time
import time



class Known(laplace_theory.TheoreticalValue):
    """ Known Values """
    
    def __init__(self, x, s, unknown, x_value):
        self.Theory = laplace_theory.TheoreticalValue(x, s, x_value)
        self.unknown = unknown
        
    def known(self):
        a_theory = self.Theory.a_theory()
        b_theory = self.Theory.b_theory()
        unknown = self.unknown
        
        known = np.ndarray((18 - len(unknown),))
        known[0] = a_theory[0][0]
        known[1] = a_theory[0][1]
        known[2] = a_theory[0][2]
        known[3] = a_theory[1][0]
        known[4] = a_theory[1][1]
        known[5] = a_theory[1][2]
        known[6] = b_theory[0]
        known[7] = b_theory[1]
        known[8] = b_theory[2]
        
        return known


class Unknown(laplace_theory.TheoreticalValue):
    """ Values Related to Unknowns """

    def __init__(self, x, s, unknown, x_value):
        self.Theory = laplace_theory.TheoreticalValue(x, s, x_value)
        self.unknown = unknown
        
    def unknown_theory(self):
        unknown = self.unknown
        a_theory = self.Theory.a_theory()
        b_theory = self.Theory.b_theory()
        
        unknown_theory = np.ndarray((len(unknown),))
        unknown_theory[0] = a_theory[0][3]
        unknown_theory[1] = a_theory[0][4]
        unknown_theory[2] = a_theory[0][5]
        unknown_theory[3] = a_theory[1][3]
        unknown_theory[4] = a_theory[1][4]
        unknown_theory[5] = a_theory[1][5]
        unknown_theory[6] = b_theory[3]
        unknown_theory[7] = b_theory[4]
        unknown_theory[8] = b_theory[5]
        
        return unknown_theory
        
    def unknown_init(self):
        unknown_theory = self.unknown_theory()
    
        e = 10000.0
        unknown_init = np.ndarray((len(unknown),))
        for i in range(len(unknown)):
            unknown_init[i] = (1 + random.uniform(-e, e)/100)*unknown_theory[i]
        
        return unknown_init


class Taylor(Known):
    """ Taylor Series Expressions """
    
    def __init__(self, x, s, unknown, x_value, unknown_init):
        self.Known = Known(x, s, unknown, x_value)
        self.x_value = x_value
        self.unknown_init = unknown_init
        
    def x_taylor_s(self, x, unknown):
        """ 2nd Order x_Taylor Series of s1 """
        x_value = self.x_value
        known = self.Known.known()

        dx = x - x_value
        
        x_taylor_s = np.ndarray((2,), 'object')
    
        x_taylor_s[0] = known[0] \
                        + known[1]*dx[0] \
                        + known[2]*dx[1] \
                        + unknown[0]*dx[0]**2/2 \
                        + unknown[1]*dx[0]*dx[1] \
                        + unknown[2]*dx[1]**2/2
               
        x_taylor_s[1] = known[3] \
                        + known[4]*dx[0] \
                        + known[5]*dx[1] \
                        + unknown[3]*dx[0]**2/2 \
                        + unknown[4]*dx[0]*dx[1] \
                        + unknown[5]*dx[1]**2/2
        
        return x_taylor_s
        
    def s_value(self):
        x_value = self.x_value
        unknown_init = self.unknown_init
        s_value = self.x_taylor_s(x_value, unknown_init)
        
        return s_value
        
    def s_taylor_u(self, s, unknown):
        """ 2nd Order x_Taylor Series of s1 """
        known = self.Known.known()
        s_value = self.s_value()
        
        ds = s - s_value
        
        s_taylor_u = known[6] \
                     + known[7]*ds[0] \
                     + known[8]*ds[1] \
                     + unknown[6]*ds[0]**2/2 \
                     + unknown[7]*ds[0]*ds[1] \
                     + unknown[8]*ds[1]**2/2
                     
        return s_taylor_u
    
    def x_taylor_u(self, x, unknown):
        """ Convolution of x_taylor_s & s_taylor_u """
        x_taylor_s = self.x_taylor_s(x, unknown)
        x_taylor_u = self.s_taylor_u(x_taylor_s, unknown)
        
        return x_taylor_u
    
 
class BoundaryConditions(Taylor):
    """ Boundary Conditions along Streamline """
    
    def __init__(self, x, s, unknown, x_value, unknown_init):
        self.Taylor = Taylor(x, s, unknown, x_value, unknown_init)
        self.PCS = self.Taylor.Known.Theory.ProblemSettings
        self.x = x
        self.unknown = unknown
        self.x_value = x_value
        self.unknown_init = unknown_init
        
    def s_boundary(self):
        x_value = self.x_value
        s_value = self.PCS.s(x_value)
        s_boundary = np.ndarray((2, len(s_value)))
        
        s_boundary[0][0] = s_value[0] - 1.0e-3
        s_boundary[0][1] = s_value[1] 
        s_boundary[1][0] = s_value[0] + 1.0e-3
        s_boundary[1][1] = s_value[1] 
        
        return s_boundary
    
    def x_boundary(self):
        x = self.x
        x_value = self.x_value
        s_boundary = self.s_boundary()
        s = self.PCS.s(x)
        
        f = np.ndarray((2, len(x),), 'object')
        for i in range(2):
            for j in range(len(x)):
                f[i][j] = s[j] - s_boundary[i][j]

        x_boundary = np.ndarray((2, len(x),))
        for i in range(2):
            for j in range(len(x)):
                x_boundary[i][j] = nsolve((f[i][0], f[i][1]), \
                                          (x[0], x[1]), \
                                          (x_value[0], x_value[1]) \
                                          )[j]
                
        return x_boundary
    
    def u_boundary(self):
        s_boundary = self.s_boundary()
        
        u_boundary = np.ndarray((2),)
        for i in range(2):
            u_boundary[i] = self.PCS.u(s_boundary[i])
        
        return u_boundary
    
    def boundary_conditions(self):
        unknown = self.unknown
        x_boundary = self.x_boundary()
        u_boundary = self.u_boundary()
        
        x_taylor_u = np.ndarray((2,), 'object')
        bc = np.ndarray((2,), 'object')
        for i in range(2):
            x_taylor_u[i] = self.Taylor.x_taylor_u(x_boundary[i], unknown)
            bc[i] = x_taylor_u[i] - u_boundary[i]
            
        return bc
        

class Derivative(Taylor):
    """ x_Taylor Series of Derivatives """
    
    def __init__(self, x, s, unknown, x_value, unknown_init):
        self.Taylor = Taylor(x, s, unknown, x_value, unknown_init)
        self.x = x
        self.s = s
        self.unknown = unknown
        
    def du_ds(self):
        x = self.x
        s = self.s
        unknown = self.unknown
        s_taylor_u = self.Taylor.s_taylor_u(s, unknown)
        x_taylor_s = self.Taylor.x_taylor_s(x, unknown)
        
        du_ds = np.ndarray((2,), 'object')
        for i in range(2):
            du_ds[i] = diff(s_taylor_u, s[i])
        
        for i in range(2):
            du_ds[i] = lambdify(s, du_ds[i], 'numpy')
            du_ds[i] = du_ds[i](x_taylor_s[0], x_taylor_s[1])
        
        return du_ds
                    
    def ddu_dds(self):
        x = self.x
        s = self.s
        unknown = self.unknown
        s_taylor_u = self.Taylor.s_taylor_u(s, unknown)
        x_taylor_s = self.Taylor.x_taylor_s(x, unknown)
        
        ddu_dds = np.ndarray((2, 2), 'object')
        ddu_dds[0][0] = diff(s_taylor_u, s[0], 2)
        ddu_dds[0][1] = diff(s_taylor_u, s[0], s[1])
        ddu_dds[1][0] = diff(s_taylor_u, s[1], s[0])
        ddu_dds[1][1] = diff(s_taylor_u, s[1], 2)
        
        for i in range(2):
            for j in range(2):
                ddu_dds[i][j] = lambdify(s, ddu_dds[i][j], 'numpy')
                ddu_dds[i][j] = ddu_dds[i][j](x_taylor_s[0], x_taylor_s[1])       
        
        return ddu_dds
       
    def ds_dx(self):
        x = self.x
        unknown = self.unknown
        x_taylor_s = self.Taylor.x_taylor_s(x, unknown)
        
        ds_dx = np.ndarray((2, 2,), 'object')
        ds_dx[0][0] = diff(x_taylor_s[0], x[0])
        ds_dx[0][1] = diff(x_taylor_s[0], x[1])
        ds_dx[1][0] = diff(x_taylor_s[1], x[0])
        ds_dx[1][1] = diff(x_taylor_s[1], x[1])
                
        return ds_dx
    
    def dx_ds(self):
        """ Inverse Matrix Library NOT Used due to High Computational Cost """
        ds_dx = self.ds_dx()
        det = ds_dx[0][0]*ds_dx[1][1] - ds_dx[0][1]*ds_dx[1][0]
        
        dx_ds = np.ndarray((2, 2), 'object')
        dx_ds[0][0] = ds_dx[1][1]/det
        dx_ds[0][1] = - ds_dx[0][1]/det
        dx_ds[1][0] = - ds_dx[1][0]/det
        dx_ds[1][1] = ds_dx[0][0]/det
    
        return dx_ds
    
    def dds_ddx(self):
        x = self.x
        unknown = self.unknown
        x_taylor_s = self.Taylor.x_taylor_s(x, unknown)
        
        dds_ddx = np.ndarray((2, 2, 2), 'object')
        for i in range(2):
            dds_ddx[i][0][0] = diff(x_taylor_s[i], x[0], 2)
            dds_ddx[i][0][1] = diff(x_taylor_s[i], x[0], x[1])
            dds_ddx[i][1][0] = diff(x_taylor_s[i], x[1], x[0])
            dds_ddx[i][1][1] = diff(x_taylor_s[i], x[1], 2)
        
        return dds_ddx
        

class Metric(Derivative):
    """ x_Taylor Series of Metrics """
    
    def __init__(self, x, s, unknown, x_value, unknown_init):
        self.Derivative = Derivative(x, s, unknown, x_value, unknown_init)
        self.x = x
    
    def supermetric(self):
        """ Superscript Metric g^ij """
        ds_dx = self.Derivative.ds_dx()
        
        ds1_dx = np.ndarray((2,), 'object')
        ds1_dx[0] = ds_dx[0][0]
        ds1_dx[1] = ds_dx[0][1]
        ds2_dx = np.ndarray((2,), 'object')
        ds2_dx[0] = ds_dx[1][0]
        ds2_dx[1] = ds_dx[1][1]
        
        supermetric = np.ndarray((2, 2,), 'object')
        supermetric[0][0] = dot(ds1_dx, ds1_dx)
        supermetric[0][1] = dot(ds1_dx, ds2_dx)
        supermetric[1][0] = dot(ds2_dx, ds1_dx)
        supermetric[1][1] = dot(ds2_dx, ds2_dx)
        
        return supermetric
    
    def dg_ds1(self):
        """ dg^ij/ds1 = dx1/ds1*dg^ij/dx1 + dx2/ds1*dg^ij/dx2 """
        dx1_ds1 = self.Derivative.dx_ds()[0][0]
        dx2_ds1 = self.Derivative.dx_ds()[1][0]
        supermetric = self.supermetric()
        x = self.x
        
        dg_dx1 = np.ndarray((2, 2), 'object')
        for i in range(2):
            for j in range(2):
                dg_dx1[i][j] = diff(supermetric[i][j], x[0]) 
                
        dg_dx2 = np.ndarray((2, 2), 'object')
        for i in range(2):
            for j in range(2):
                dg_dx2[i][j] = diff(supermetric[i][j], x[1])
                    
        dg_ds1 = np.ndarray((2, 2,), 'object')
        for i in range(2):
            for j in range(2):
                dg_ds1[i][j] = dx1_ds1*dg_dx1[i][j] \
                               + dx2_ds1*dg_dx2[i][j]
        
        return dg_ds1
        

class Laplacian(Metric):
    """ x_Taylor Series of Laplacian """
    
    def __init__(self, x, s, unknown, x_value, unknown_init):
        self.Metric = Metric(x, s, unknown, x_value, unknown_init)
        self.Derivative = self.Metric.Derivative
        
    def laplacian_u(self):
        """ 2*g11*g22*u,11 + (g22*g11,1 - g11*g22,1)*u,1 """
        du_ds1 = self.Derivative.du_ds()[0]
        ddu_dds1 = self.Derivative.ddu_dds()[0][0]
        
#        g11 = self.Metric.supermetric()[0][0]
#        g22 = self.Metric.supermetric()[1][1]
#        dg11_ds1 = self.Metric.dg_ds1()[0][0]
#        dg22_ds1 = self.Metric.dg_ds1()[1][1]
#
#        laplacian_u = 2*g11*g22*ddu_dds1 \
#                      + (g22*dg11_ds1 - g11*dg22_ds1)*du_ds1

        ds1_dx1 = self.Derivative.ds_dx()[0][0]
        ds1_dx2 = self.Derivative.ds_dx()[0][1]
        dds1_ddx1 = self.Derivative.dds_ddx()[0][0][0]
        dds1_ddx2 = self.Derivative.dds_ddx()[0][1][1]

        laplacian_u = ((ds1_dx1)**2 + (ds1_dx2)**2)*ddu_dds1 \
                      + (dds1_ddx1 + dds1_ddx2)*du_ds1
        
        return laplacian_u


class GoverningEquations(Laplacian):
    """ Derive Governing Equations """
    
    def __init__(self, x, s, unknown, x_value, unknown_init):
        self.Laplacian = Laplacian(x, s, unknown, x_value, unknown_init)
        self.Metric = self.Laplacian.Metric
        self.Derivative = self.Laplacian.Metric.Derivative
        self.Taylor = self.Laplacian.Metric.Derivative.Taylor
        self.x =  x
        self.x_value = x_value

    def governing_equation_0(self):
        """ 1st Order x_Taylor Series of g_12 """
        du_ds2 = self.Derivative.du_ds()[1]
        x = self.x
        x_value = self.x_value
        
        coeff_du_ds2 = np.ndarray((6), 'object')
#        coeff_du_ds2[0] = du_ds2
        coeff_du_ds2[1] = diff(du_ds2, x[0])
        coeff_du_ds2[2] = diff(du_ds2, x[1])
#        coeff_du_ds2[3] = diff(du_ds2, x[0], 2)
#        coeff_du_ds2[4] = diff(du_ds2, x[0], x[1])
#        coeff_du_ds2[5] = diff(du_ds2, x[1], 2)
        
        for i in range(len(coeff_du_ds2)):
            coeff_du_ds2[i] = lambdify(x, coeff_du_ds2[i], 'numpy')
            coeff_du_ds2[i] = coeff_du_ds2[i](x_value[0], x_value[1])
            
        return coeff_du_ds2
        
    def governing_equation_1(self):
        """ 1st Order x_Taylor Series of g_12 """
        g12 = self.Metric.supermetric()[0][1]
        x = self.x
        x_value = self.x_value
        
        coeff_g12 = np.ndarray((6), 'object')
#        coeff_g12[0] = g12
        coeff_g12[1] = diff(g12, x[0])
        coeff_g12[2] = diff(g12, x[1])
        coeff_g12[3] = diff(g12, x[0], 2)
        coeff_g12[4] = diff(g12, x[0], x[1])
#        coeff_g12[5] = diff(g12, x[1], 2)
        
        for i in range(len(coeff_g12)):
            coeff_g12[i] = lambdify(x, coeff_g12[i], 'numpy')
            coeff_g12[i] = coeff_g12[i](x_value[0], x_value[1])
            
        return coeff_g12
    
    def governing_equation_2(self):
        """ 1st Order x_Taylor Series of g_12 """
        laplacian_u = self.Laplacian.laplacian_u()
        x = self.x
        x_value = self.x_value
        
        coeff_laplacian_u = np.ndarray((6), 'object')
        coeff_laplacian_u[0] = laplacian_u
#        coeff_laplacian_u[1] = diff(laplacian_u, x[0])
#        coeff_laplacian_u[2] = diff(laplacian_u, x[1])
#        coeff_laplacian_u[3] = diff(laplacian_u, x[0], 2)
#        coeff_laplacian_u[4] = diff(laplacian_u, x[0], x[1])
#        coeff_laplacian_u[5] = diff(laplacian_u, x[1], 2)
        
        for i in range(len(coeff_laplacian_u)):
            coeff_laplacian_u[i] = lambdify(x, coeff_laplacian_u[i], 'numpy')
            coeff_laplacian_u[i] = coeff_laplacian_u[i](x_value[0], x_value[1])
            
        return coeff_laplacian_u


class Solve(BoundaryConditions, GoverningEquations):
    """ Solve BVP on Line Element by Newton's Method """
    
    def __init__(self, x, s, unknown, x_value, unknown_init):
        self.BC = BoundaryConditions(x, s, unknown, x_value, unknown_init)
        self.GE = GoverningEquations(x, s, unknown, x_value, unknown_init)
        self.unknown = unknown
        self.unknown_init = unknown_init
    
    def f(self):
        unknown = self.unknown
        bc = self.BC.boundary_conditions()
        ge0 = self.GE.governing_equation_0()
        ge1 = self.GE.governing_equation_1()
        ge2 = self.GE.governing_equation_2()
        
        f = np.ndarray((len(unknown),), 'object')
        f[0] = bc[0]
        f[1] = bc[1]
        f[2] = ge0[1]
        f[3] = ge0[2]
        f[4] = ge1[1]
        f[5] = ge1[2]
        f[6] = ge1[3]
        f[7] = ge1[4]
        f[8] = ge2[0]
        
        return f
    
    def A(self, unknown_temp):
        unknown = self.unknown
        f = self.f()
        
        A = np.ndarray((len(f), len(unknown),), 'object')
        for i in range(len(f)):
            for j in range(len(unknown)):
                A[i][j] = diff(f[i], unknown[j])
                A[i][j] = lambdify(unknown, A[i][j], 'numpy')
                A[i][j] = A[i][j](unknown_temp[0],
                                  unknown_temp[1],
                                  unknown_temp[2],
                                  unknown_temp[3],
                                  unknown_temp[4],
                                  unknown_temp[5],
                                  unknown_temp[6],
                                  unknown_temp[7],
                                  unknown_temp[8],
                                  )
        A = A.astype('double')
        
        return A
    
    def b(self, unknown_temp):
        unknown = self.unknown
        f = self.f()
        
        b = np.ndarray((len(f),), 'object')
        for i in range(len(f)):
            b[i] = -f[i]
            for j in range(len(unknown)):
                b[i] += diff(f[i], unknown[j])*unknown[j]
            b[i] = lambdify(unknown, b[i], 'numpy')
            b[i] = b[i](unknown_temp[0],
                        unknown_temp[1],
                        unknown_temp[2],
                        unknown_temp[3],
                        unknown_temp[4],
                        unknown_temp[5],
                        unknown_temp[6],
                        unknown_temp[7],
                        unknown_temp[8],
                        )
        b = b.astype('double')
    
        return b    
    
    def error(self, unknown_temp):
        unknown = self.unknown
        f = self.f()
        
        error = np.ndarray((len(f),), 'object')
        for i in range(len(f)):
            error[i] = lambdify(unknown, f[i], 'numpy')
            error[i] = error[i](unknown_temp[0],
                                unknown_temp[1],
                                unknown_temp[2],
                                unknown_temp[3],
                                unknown_temp[4],
                                unknown_temp[5],
                                unknown_temp[6],
                                unknown_temp[7],
                                unknown_temp[8],
                                )
        error = norm(error)
        
        return error
    
    def solution(self):
        unknown_init = self.unknown_init
        unknown_temp = unknown_init
        error = self.error(unknown_temp)
        
        while error > 1.0e-8:
            A = self.A(unknown_temp)
            b = self.b(unknown_temp)
            unknown_temp = solve(A, b)        
            error = self.error(unknown_temp)
        
        solution = unknown_temp
        
        return solution

        

if __name__ == '__main__':
    
    t0 = time.time()
    
    x = np.ndarray((2,), 'object')
    x[0] = Symbol('x1', real = True)
    x[1] = Symbol('x2', real = True)
    
    s = np.ndarray((2,), 'object')
    s[0] = Symbol('s1', real = True)
    s[1] = Symbol('s2', real = True)
    
    unknown = np.ndarray((9,), 'object')
    unknown[0] = Symbol('a1_11', real = True)
    unknown[1] = Symbol('a1_12', real = True)
    unknown[2] = Symbol('a1_22', real = True)
    unknown[3] = Symbol('a2_11', real = True)
    unknown[4] = Symbol('a2_12', real = True)
    unknown[5] = Symbol('a2_22', real = True)
    unknown[6] = Symbol('b11', real = True)
    unknown[7] = Symbol('b12', real = True)
    unknown[8] = Symbol('b22', real = True)
    
    n = 1
    
    x_target = np.ndarray((len(x),))
    
    x_target_array = np.ndarray((n, n, len(x),))
    
    unknown_theory_array = np.ndarray((n, n, len(unknown)))
    unknown_init_array = np.ndarray((n, n, len(unknown)))
    unknown_experiment_array = np.ndarray((n, n, len(unknown)))
    
    error_init_array = np.ndarray((n, n, 1))
    error_experiment_array = np.ndarray((n, n, 1))
    
    abs_eigvals_A_init_array = np.ndarray((n, n, len(unknown)))
    
    
    def relative_error(a, b):
        
        relative_error = round(norm(b - a)/norm(a), 4)*100
        
        return relative_error
    
    
    for i in range(n):
        for j in range(n):
            x_target[0] = 1.0 + i/n
            x_target[1] = 1.0 + j/n
            
            ################################################
            Unknown_call = Unknown(x, s, unknown, x_target)
            ################################################
            unknown_theory = Unknown_call.unknown_theory()
            unknown_init = Unknown_call.unknown_init()
        
        
#            ##################################################################################
#            BoundaryConditions_call = BoundaryConditions(x, s, unknown, x_target, unknown_init)
#            ##################################################################################
#            boundary_condtions = BoundaryConditions_call.boundary_conditions()
#            
#            ####################################################################
#            Derivative_call = Derivative(x, s, unknown, x_target, unknown_init)
#            ####################################################################
#            du_ds2 = Derivative_call.du_ds()[1]
#            
#            ############################################################
#            Metric_call = Metric(x, s, unknown, x_target, unknown_init)
#            ############################################################
#            g12 = Metric_call.supermetric()[0][1]
#            
#            ##################################################################
#            Laplacian_call = Laplacian(x, s, unknown, x_target, unknown_init)
#            ##################################################################
#            laplacian_u = Laplacian_call.laplacian_u()
        
        
            ####################################################################
            Solve_call = Solve(x, s, unknown, x_target, unknown_init)
            ####################################################################
            unknown_experiment = Solve_call.solution()
            A_init = Solve_call.A(unknown_init)
            eigvals_A_init = eigvals(A_init)
            abs_eigvals_A_init = abs(eigvals_A_init)
            
            error_init = relative_error(unknown_theory, unknown_init)
            error_experiment = relative_error(unknown_theory, unknown_experiment)
            
            for k in range(len(x)):
                x_target_array[i][j][k] = x_target[k]
    
            for k in range(len(unknown)):
                unknown_theory_array[i][j][k] = unknown_theory[k]
                unknown_init_array[i][j][k] = unknown_init[k]
                unknown_experiment_array[i][j][k] = unknown_experiment[k]
                abs_eigvals_A_init[k] = round(abs_eigvals_A_init[k], 8)
                abs_eigvals_A_init_array[i][j][k] = abs_eigvals_A_init[k]
                
            for k in range(1):
                error_init_array[i][j][k] = error_init
                error_experiment_array[i][j][k] = error_experiment

#    print('Boundary Condition = ')
#    for i in range(2):    
#        display(boundary_condtions[i])
#    print('')
#
#    print('du_ds2 = ')
#    display(du_ds2)
#    print('')
#    
#    print('g12 = ')
#    display(g12)
#    print('')
#    
#    print('laplcian_u = ')
#    display(laplacian_u)
#    print('')
    

    print('unknown_theory = ')
    print(unknown_theory_array)
    print('')
            
    print('unknown_init = ')
    print(unknown_init_array)
    print('')
          
    print('error_init(%) = ')
    print(error_init_array)
    print()    
    print('unknown_experiment = ')
    print(unknown_experiment_array)
    print('')
          
    print('error_experiment(%) = ')
    print(error_experiment_array)
    print('')
    
#    print('A_init = ')
#    print(A_init)
#    print('')
    
    print('abs_eigvals_A_init = ')
    print(abs_eigvals_A_init_array)
    print('')
            
            
    t1 = time.time()
    
    print('Elapsed Time = ')
    print(round(t1 - t0), '(s)')
    print('')






        
    









