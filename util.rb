#!/usr/local/bin/ruby
# $Id$

class TermWSDL
   attr_reader :name, :wsdl
   def initialize(name, wsdl)
      @name = name
      @wsdl = wsdl
   end
end

class CGI
	def valid?( param, idx = 0 )
		self[param] and self[param][idx] and self[param][idx].length > 0
	end
end
