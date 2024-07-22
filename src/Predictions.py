# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 14:38:22 2024

@author: Cesi
"""

import numpy as np
import scipy as sp

def cov_exp(beta, l, x1, x2 = None):
    if x2 is None:
        x2 = np.copy(x1)
    n1, p = x1.shape
    n2 = len(x2)
    cov = np.zeros((n1, n2))
    for i in range(n1):
        for j in range(n2):
            cov[i,j] = np.exp(-np.dot(beta, (x1[i]-x2[j])**2))/l
    return cov

def y_pred(posterior, x_star, xf, xc, tc, z):
    
    n = len(xf)
    n_star = len(x_star)
    
    # Variables de calibration à posteriori
    tf = np.tile(posterior["tf"], (n, 1))
    tf_star = np.tile(posterior["tf"], (n_star, 1))

    beta_eta = posterior["beta_eta"]
    beta_delta = posterior["beta_delta"]
    lambda_eta = posterior["lambda_eta"]
    lambda_delta = posterior["lambda_delta"]
    lambda_eps = posterior["lambda_eps"]

    # Combinaison des données observées et simulées
    XTfc = np.concatenate((np.concatenate((xf, xc)), np.concatenate((tf, tc))), axis = 1)

    # Combinaison des points à prédire x_star et des variables incertaines à posteriori
    XT_star = np.concatenate((x_star, tf_star), axis = 1)

    # Matrice de covariance de z
    sig_eta = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XTfc)
    sig_delta = cov_exp(beta = beta_delta, l = lambda_delta, x1 = xf)
    sigma_eps = np.eye(n)/lambda_eps
    sig_z = np.copy(sig_eta)
    sig_z[:n, :n] += sig_delta+sigma_eps

    # Decomposition de Cholesky de la matrice de covariance de z
    chol, low = sp.linalg.cho_factor(sig_z, lower = True)

    # Calcul de la moyenne et de la covariance de y_star sachant z
    
    K = sp.linalg.cho_solve((chol, low), z)
    
    L = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XTfc, x2 = XT_star)
    L[:n, :n_star] += cov_exp(beta = beta_delta, l = lambda_delta, x1 = xf, x2 = x_star)
    
    M_y = np.dot(L.T, sp.linalg.cho_solve((chol, low), L))
    mu_y_star = np.dot(L.T, K)
    
    sig_eta_star = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XT_star)
    sig_delta_star = cov_exp(beta = beta_delta, l = lambda_delta, x1 = x_star)
    cov_y_star = sig_eta_star+sig_delta_star+np.eye(n_star)/lambda_eps

    cov_y_star -= M_y

    y_star_std = np.random.multivariate_normal(mean = mu_y_star, cov = cov_y_star)

    return y_star_std

def eta_delta_pred(posterior, x_star, xf, xc, tc, z):
    
    n = len(xf)
    n_star = len(x_star)
    
    # Variables de calibration à posteriori
    tf = np.tile(posterior["tf"], (n, 1))
    tf_star = np.tile(posterior["tf"], (n_star, 1))

    beta_eta = posterior["beta_eta"]
    beta_delta = posterior["beta_delta"]
    lambda_eta = posterior["lambda_eta"]
    lambda_delta = posterior["lambda_delta"]
    lambda_eps = posterior["lambda_eps"]

    # Combinaison des données observées et simulées
    XTfc = np.concatenate((np.concatenate((xf, xc)), np.concatenate((tf, tc))), axis = 1)

    # Combinaison des points à prédire x_star et des variables incertaines à posteriori
    XT_star = np.concatenate((x_star, tf_star), axis = 1)

    # Matrice de covariance de z
    sig_eta = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XTfc)
    sig_delta = cov_exp(beta = beta_delta, l = lambda_delta, x1 = xf)
    sigma_eps = np.eye(n)/lambda_eps
    sig_z = np.copy(sig_eta)
    sig_z[:n, :n] += sig_delta+sigma_eps

    # Decomposition de Cholesky de la matrice de covariance de z
    chol, low = sp.linalg.cho_factor(sig_z, lower = True)

    # Calcul de la moyenne et de la covariance de y_star sachant z
    
    K = sp.linalg.cho_solve((chol, low), z)
    
    L = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XTfc, x2 = XT_star)
    L[:n, :n_star] += cov_exp(beta = beta_delta, l = lambda_delta, x1 = xf, x2 = x_star)
    
    M_y = np.dot(L.T, sp.linalg.cho_solve((chol, low), L))
    mu_y_star = np.dot(L.T, K)
    
    sig_eta_star = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XT_star)
    sig_delta_star = cov_exp(beta = beta_delta, l = lambda_delta, x1 = x_star)
    cov_y_star = sig_eta_star+sig_delta_star

    cov_y_star -= M_y

    y_star_std = np.random.multivariate_normal(mean = mu_y_star, cov = cov_y_star)

    return y_star_std

def eta_pred(posterior, x_star, xf, xc, tc, z):
    
    n = len(xf)
    n_star = len(x_star)
    
    # Variables de calibration à posteriori
    tf = np.tile(posterior["tf"], (n, 1))
    tf_star = np.tile(posterior["tf"], (n_star, 1))

    beta_eta = posterior["beta_eta"]
    beta_delta = posterior["beta_delta"]
    lambda_eta = posterior["lambda_eta"]
    lambda_delta = posterior["lambda_delta"]
    lambda_eps = posterior["lambda_eps"]

    # Combinaison des données observées et simulées
    XTfc = np.concatenate((np.concatenate((xf, xc)), np.concatenate((tf, tc))), axis = 1)

    # Combinaison des points à prédire x_star et des variables incertaines à posteriori
    XT_star = np.concatenate((x_star, tf_star), axis = 1)

    # Matrice de covariance de z
    sig_eta = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XTfc)
    sig_delta = cov_exp(beta = beta_delta, l = lambda_delta, x1 = xf)
    sigma_eps = np.eye(n)/lambda_eps
    sig_z = np.copy(sig_eta)
    sig_z[:n, :n] += sig_delta+sigma_eps

    # Decomposition de Cholesky de la matrice de covariance de z
    chol, low = sp.linalg.cho_factor(sig_z, lower = True)

    # Calcul de la moyenne et de la covariance de y_star sachant z
    
    K = sp.linalg.cho_solve((chol, low), z)
    
    L = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XTfc, x2 = XT_star)
    
    M_eta = np.dot(L.T, sp.linalg.cho_solve((chol, low), L))
    mu_eta_star = np.dot(L.T, K)
    
    sig_eta_star = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XT_star)
    cov_eta_star = sig_eta_star

    cov_eta_star -= M_eta

    eta_star_std = np.random.multivariate_normal(mean = mu_eta_star, cov = cov_eta_star)

    return eta_star_std

def delta_pred(posterior, x_star, xf, xc, tc, z):
    
    m = len(xc)
    n = len(xf)
    n_star = len(x_star)
    
    # Variables de calibration à posteriori
    tf = np.tile(posterior["tf"], (n, 1))

    beta_eta = posterior["beta_eta"]
    beta_delta = posterior["beta_delta"]
    lambda_eta = posterior["lambda_eta"]
    lambda_delta = posterior["lambda_delta"]
    lambda_eps = posterior["lambda_eps"]

    # Combinaison des données observées et simulées
    XTfc = np.concatenate((np.concatenate((xf, xc)), np.concatenate((tf, tc))), axis = 1)

    # Matrice de covariance de z
    sig_eta = cov_exp(beta = beta_eta, l = lambda_eta, x1 = XTfc)
    sig_delta = cov_exp(beta = beta_delta, l = lambda_delta, x1 = xf)
    sigma_eps = np.eye(n)/lambda_eps
    sig_z = np.copy(sig_eta)
    sig_z[:n, :n] += sig_delta+sigma_eps

    # Decomposition de Cholesky de la matrice de covariance de z
    chol, low = sp.linalg.cho_factor(sig_z, lower = True)

    # Calcul de la moyenne et de la covariance de y_star sachant z
    
    K = sp.linalg.cho_solve((chol, low), z)
    
    L = cov_exp(beta = beta_delta, l = lambda_delta, x1 = xf, x2 = x_star)
    L = np.concatenate((L, np.zeros((m, n_star))))
    
    M_delta = np.dot(L.T, sp.linalg.cho_solve((chol, low), L))
    mu_delta_star = np.dot(L.T, K)
    
    sig_delta_star = cov_exp(beta = beta_delta, l = lambda_delta, x1 = x_star)
    cov_delta_star = sig_delta_star

    cov_delta_star -= M_delta

    delta_star_std = np.random.multivariate_normal(mean = mu_delta_star, cov = cov_delta_star)

    return delta_star_std