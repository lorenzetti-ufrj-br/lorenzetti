#ifndef Collection_h
#define Collection_h

#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/EDM.h"
#include <map>
#include <memory>
#include <iostream>
#include <stdexcept>

namespace SG {

  template<class T>
  class Collection : public SG::DataHandle {  
  public:
    /*! Constructor */
    Collection() = default;
    
    /*! Destructor - releases all owned objects */
    virtual ~Collection();
    
    /*! Add a new object into the collection with unique ID and link parent container */
    bool insert(unsigned long int id, T* obj);

    /*! Retrieve object pointer by ID */
    bool retrieve(unsigned long int id, T*& obj) const;

    /*! Check if ID exists in collection */
    bool count(unsigned long int id) const;

    /*! Access element by ID with bounds checking */
    const T* at(unsigned long int id) const;
    T* at(unsigned long int id);

    /*! Size of collection */
    size_t size() const;

    /*! Check if collection is empty */
    bool empty() const;

    /*! Clear collection and release memory */
    void clear();

    /*! Iterator access */
    typename std::map<unsigned long int, T*>::const_iterator begin() const { return m_collection.begin(); }
    typename std::map<unsigned long int, T*>::const_iterator end() const { return m_collection.end(); }
    typename std::map<unsigned long int, T*>::iterator begin() { return m_collection.begin(); }
    typename std::map<unsigned long int, T*>::iterator end() { return m_collection.end(); }
    
    /*! Underlying map dereference */
    const std::map<unsigned long int, T*>& operator*() const;

  private:
    /*! Hold all object pointers */
    std::map<unsigned long int, T*> m_collection;
  };

  template<class T>
  Collection<T>::~Collection() {
    clear();
  }

  template<class T>
  inline void Collection<T>::clear() {
    for (auto& p : m_collection) {
      if (p.second) {
        delete p.second;
      }
    }
    m_collection.clear();
  }

  template<class T>
  inline bool Collection<T>::insert(unsigned long int id, T* obj) {
    if (m_collection.count(id)) {
      return false;
    }
    if (obj) {
      auto* edmBase = dynamic_cast<Gaugi::EDM*>(obj);
      if (edmBase) {
        edmBase->setContainer(this);
      }
    }
    m_collection.insert(std::make_pair(id, obj));
    return true;
  }

  template<class T>
  inline bool Collection<T>::retrieve(unsigned long int id, T*& obj) const {
    auto it = m_collection.find(id);
    if (it != m_collection.end()) {
      obj = it->second;
      return true;
    } else {
      obj = nullptr;
      return false;
    }
  }

  template<class T>
  inline bool Collection<T>::count(unsigned long int id) const {
    return m_collection.count(id) > 0;
  }

  template<class T>
  inline const T* Collection<T>::at(unsigned long int id) const {
    auto it = m_collection.find(id);
    if (it != m_collection.end()) {
      return it->second;
    }
    throw std::out_of_range("Collection::at() - ID not found");
  }

  template<class T>
  inline T* Collection<T>::at(unsigned long int id) {
    auto it = m_collection.find(id);
    if (it != m_collection.end()) {
      return it->second;
    }
    throw std::out_of_range("Collection::at() - ID not found");
  }

  template<class T>
  inline size_t Collection<T>::size() const {
    return m_collection.size();
  }

  template<class T>
  inline bool Collection<T>::empty() const {
    return m_collection.empty();
  }

  template<class T>
  inline const std::map<unsigned long int, T*>& Collection<T>::operator*() const {
    return m_collection;
  }

} // namespace SG

#endif