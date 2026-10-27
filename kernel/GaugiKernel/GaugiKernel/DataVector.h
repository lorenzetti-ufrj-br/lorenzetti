#ifndef DataVector_h
#define DataVector_h

#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/EDM.h"
#include <vector>
#include <memory>
#include <iostream>
#include <stdexcept>

namespace SG {

  /**
   * @class DataVector
   * @brief Type-safe polymorphic container for Event Data Model (EDM) objects.
   *
   * Manages lifecycle of heap-allocated elements and automatically establishes
   * the parent container reference on every contained element.
   */
  template<class T>
  class DataVector : public DataHandle {  
  public:
    using base_type = T;
    using value_type = const T*;
    
    /*! Constructor */
    DataVector() = default;

    /*! Destructor - releases all owned elements */
    virtual ~DataVector();
    
    /*! Return the number of objects in this container */
    size_t size() const;

    /*! Check if container is empty */
    bool empty() const;
    
    /*! Add a new object into the container and attach container reference */
    void push_back(const T* obj);

    /*! Access element by index with bounds checking */
    const T* at(size_t index) const;

    /*! Direct indexing operator */
    const T* operator[](size_t index) const;

    /*! Access first element */
    const T* front() const { return m_data.empty() ? nullptr : m_data.front(); }

    /*! Access last element */
    const T* back() const { return m_data.empty() ? nullptr : m_data.back(); }

    /*! Iterator access */
    typename std::vector<const T*>::const_iterator begin() const { return m_data.begin(); }
    typename std::vector<const T*>::const_iterator end() const { return m_data.end(); }

    /*! Underlying vector dereference */
    const std::vector<const T*>& operator*() const;

  private:
    /*! Hold all object pointers */
    std::vector<const T*> m_data;
  };

  
  template<class T>
  DataVector<T>::~DataVector() {
    for (auto obj : m_data) {
      if (obj) {
        delete obj;
      }
    }
  }

  template<class T>
  inline size_t DataVector<T>::size() const {
    return m_data.size();
  }

  template<class T>
  inline bool DataVector<T>::empty() const {
    return m_data.empty();
  }
  
  template<class T>
  inline void DataVector<T>::push_back(const T* obj) {
    if (obj) {
      // Attach this container as the parent container of the EDM element
      auto* nonConstObj = const_cast<T*>(obj);
      auto* edmBase = dynamic_cast<Gaugi::EDM*>(nonConstObj);
      if (edmBase) {
        edmBase->setContainer(this);
      }
    }
    m_data.push_back(obj);
  }

  template<class T>
  inline const T* DataVector<T>::at(size_t index) const {
    if (index >= m_data.size()) {
      throw std::out_of_range("DataVector::at() - index out of range");
    }
    return m_data.at(index);
  }

  template<class T>
  inline const T* DataVector<T>::operator[](size_t index) const {
    return m_data[index];
  }

  template<class T>
  inline const std::vector<const T*>& DataVector<T>::operator*() const {
    return m_data;
  }

} // namespace SG

#endif
