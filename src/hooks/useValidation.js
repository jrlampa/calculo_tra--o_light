/**
 * The above code defines custom hooks for form validation and traversal validation in React.
 * @param [initialValues] - The `initialValues` parameter in the `useValidation` hook refers to the
 * initial values of the form fields that you want to validate. It is an object where each key
 * represents a form field and the corresponding value is the initial value of that field.
 * @param [validationRules] - The `validationRules` parameter is an object that contains the rules for
 * validating each field in a form. Each key in the object represents a field in the form, and the
 * corresponding value is an object that defines the validation rules for that field. Here are the
 * possible validation rules that can be defined for
 * @returns The `useValidation` hook returns an object with the following properties and functions:
 * - `values`: current form values
 * - `errors`: validation errors for each field
 * - `touched`: tracks which fields have been touched
 * - `isValid`: boolean indicating if the form is valid
 * - `isDirty`: boolean indicating if the form has been modified
 * - `setValue`: function to update a
 */
import { useState, useCallback, useMemo } from 'react'

/**
 * Hook customizado para validação de formulários
 * @param {Object} initialValues - Valores iniciais
 * @param {Object} validationRules - Regras de validação
 * @returns {Object} - Estado e funções de validação
 */
export const useValidation = (initialValues = {}, validationRules = {}) => {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})

  // Função de validação
  const validate = useCallback((fieldValues = values) => {
    const newErrors = {}
    
    Object.keys(validationRules).forEach(field => {
      const rules = validationRules[field]
      const value = fieldValues[field]
      
      if (rules.required && (!value || value.toString().trim() === '')) {
        newErrors[field] = rules.required || 'Campo obrigatório'
      } else if (rules.pattern && !rules.pattern.test(value)) {
        newErrors[field] = rules.pattern.message || 'Valor inválido'
      } else if (rules.min && parseFloat(value) < rules.min) {
        newErrors[field] = `Valor mínimo: ${rules.min}`
      } else if (rules.max && parseFloat(value) > rules.max) {
        newErrors[field] = `Valor máximo: ${rules.max}`
      } else if (rules.custom && !rules.custom(value)) {
        newErrors[field] = rules.custom.message || 'Valor inválido'
      }
    })
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [values, validationRules])

  // Validar campo específico
  const validateField = useCallback((field, value) => {
    const rules = validationRules[field]
    if (!rules) return true
    
    let error = null
    
    if (rules.required && (!value || value.toString().trim() === '')) {
      error = rules.required || 'Campo obrigatório'
    } else if (rules.pattern && !rules.pattern.test(value)) {
      error = rules.pattern.message || 'Valor inválido'
    } else if (rules.min && parseFloat(value) < rules.min) {
      error = `Valor mínimo: ${rules.min}`
    } else if (rules.max && parseFloat(value) > rules.max) {
      error = `Valor máximo: ${rules.max}`
    } else if (rules.custom && !rules.custom(value)) {
      error = rules.custom.message || 'Valor inválido'
    }
    
    setErrors(prev => ({ ...prev, [field]: error }))
    return !error
  }, [validationRules])

  // Atualizar valor
  const setValue = useCallback((field, value) => {
    setValues(prev => ({ ...prev, [field]: value }))
    if (touched[field]) {
      validateField(field, value)
    }
  }, [touched, validateField])

  // Atualizar múltiplos valores
  const updateValues = useCallback((newValues) => {
    setValues(prev => ({ ...prev, ...newValues }))
    Object.keys(newValues).forEach(field => {
      if (touched[field]) {
        validateField(field, newValues[field])
      }
    })
  }, [touched, validateField])

  // Marcar campo como tocado
  const setFieldTouched = useCallback((field) => {
    setTouched(prev => ({ ...prev, [field]: true }))
    validateField(field, values[field])
  }, [values, validateField])

  // Marcar todos os campos como tocados
  const setAllTouched = useCallback(() => {
    setTouched(Object.keys(validationRules).reduce((acc, field) => ({ ...acc, [field]: true }), {}))
    validate()
  }, [validationRules, validate])

  // Resetar validação
  const resetValidation = useCallback(() => {
    setErrors({})
    setTouched({})
  }, [])

  // Verificar se formulário é válido
  const isValid = useMemo(() => {
    return Object.keys(errors).every(field => !errors[field])
  }, [errors])

  // Verificar se formulário está sujo
  const isDirty = useMemo(() => {
    return JSON.stringify(values) !== JSON.stringify(initialValues)
  }, [values, initialValues])

  return {
    values,
    errors,
    touched,
    isValid,
    isDirty,
    setValue,
    setValues: updateValues,
    setFieldTouched,
    setAllTouched,
    validate,
    validateField,
    resetValidation
  }
}

/**
 * Hook customizado para validação de travessias
 * @param {Array} travessias - Array de travessias
 * @returns {Object} - Estado e funções de validação
 */
export const useTravessiaValidation = (travessias = []) => {
  const [errors, setErrors] = useState({})

  const validateTravessia = useCallback((index, campo, valor) => {
    const fieldKey = `${index}-${campo}`
    let error = null

    // Validação de campos numéricos
    if (campo === 'vao' || campo === 'flecha' || campo === 'angulo') {
      const numValue = parseFloat(valor)
      
      if (valor && isNaN(numValue)) {
        error = 'Valor numérico inválido'
      } else if (campo === 'vao' && numValue < 0) {
        error = 'Vão não pode ser negativo'
      } else if (campo === 'vao' && numValue > 1000) {
        error = 'Vão muito grande (máx: 1000m)'
      } else if (campo === 'flecha' && numValue < 0) {
        error = 'Flecha não pode ser negativa'
      } else if (campo === 'flecha' && numValue > 50) {
        error = 'Flecha muito grande (máx: 50m)'
      } else if (campo === 'angulo' && numValue < 0) {
        error = 'Ângulo não pode ser negativo'
      } else if (campo === 'angulo' && numValue > 360) {
        error = 'Ângulo inválido (máx: 360°)'
      }
    }

    // Validação de campos de texto
    if (campo === 'tipoRede' || campo === 'tipoCabo') {
      if (valor && valor.length > 50) {
        error = 'Texto muito longo'
      }
    }

    setErrors(prev => ({ ...prev, [fieldKey]: error }))
    return !error
  }, [])

  const validateAllTravessias = useCallback(() => {
    const newErrors = {}
    
    travessias.forEach((travessia, index) => {
      Object.keys(travessia).forEach(campo => {
        const fieldKey = `${index}-${campo}`
        let error = null

        if (campo === 'vao' || campo === 'flecha' || campo === 'angulo') {
          const numValue = parseFloat(travessia[campo])
          
          if (travessia[campo] && isNaN(numValue)) {
            error = 'Valor numérico inválido'
          } else if (campo === 'vao' && numValue < 0) {
            error = 'Vão não pode ser negativo'
          } else if (campo === 'vao' && numValue > 1000) {
            error = 'Vão muito grande (máx: 1000m)'
          } else if (campo === 'flecha' && numValue < 0) {
            error = 'Flecha não pode ser negativa'
          } else if (campo === 'flecha' && numValue > 50) {
            error = 'Flecha muito grande (máx: 50m)'
          } else if (campo === 'angulo' && numValue < 0) {
            error = 'Ângulo não pode ser negativo'
          } else if (campo === 'angulo' && numValue > 360) {
            error = 'Ângulo inválido (máx: 360°)'
          }
        }

        if (campo === 'tipoRede' || campo === 'tipoCabo') {
          if (travessia[campo] && travessia[campo].length > 50) {
            error = 'Texto muito longo'
          }
        }

        if (error) {
          newErrors[fieldKey] = error
        }
      })
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [travessias])

  const getError = useCallback((index, campo) => {
    return errors[`${index}-${campo}`]
  }, [errors])

  const hasErrors = useMemo(() => {
    return Object.keys(errors).length > 0
  }, [errors])

  const clearErrors = useCallback(() => {
    setErrors({})
  }, [])

  return {
    errors,
    hasErrors,
    validateTravessia,
    validateAllTravessias,
    getError,
    clearErrors
  }
}
