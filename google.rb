#!/usr/local/bin/ruby
# $Id$

require 'cgi'
require 'erb'

class CGI
	def valid?( param, idx = 0 )
		self[param] and self[param][idx] and self[param][idx].length > 0
	end
end

class TermWSDL
   attr_reader :name, :wsdl
   def initialize ( name, wsdl )
      @name = name
      @wsdl = wsdl
   end
end

module GoogleCGI
	class GoogleBase
		include ERB::Util

		def initialize ( cgi, rhtml )
			@cgi, @rhtml = cgi, rhtml
			STDERR.puts "#{self.class}::new() ..."
		end
		
		def eval_rhtml
			rhtml = File::open( @rhtml ) {|f| f.read }
			ERB::new( rhtml ).result( binding )
		end
	end

	class GoogleForm < GoogleBase; end

	class GoogleDummy < GoogleBase
		def initialize ( cgi, rhtml )
			super
			@message = '<p class="message">検索処理中です。しばらくお待ちください。</p>'
		end
	end
	
	class GoogleSearch < GoogleBase
		MAX = 10
		MAX_PAGE = 20
		BOUNDARY = 'google_cgi'
		GOOGLE_KEY = File.open("/home/masao/.google_key").read.chomp

		def initialize ( cgi, rhtml )
			super

			# 時間がかかる処理になるので、multipart/x-mixed-replace で
			# ブラウザに渡しておく。
#  			print @cgi.header( "multipart/x-mixed-replace;boundary=#{BOUNDARY}" )
#  			print "--#{BOUNDARY}\n"
#  			print @cgi.header( 'text/html; charset=utf-8' )
#  			dummy = GoogleDummy::new( @cgi.clone, "./skel/google.rhtml" )
#  			print dummy.eval_rhtml
#  			print "\n--#{BOUNDARY}\n"

			require 'uconv'
			require 'soap/wsdlDriver'
			require 'GoogleSearch'

			@wordlist = word_search
			@result = google_search

			@result.instance_variables.each do |v|
				v.sub!( /^@/, '' )
				instance_eval %Q{
					def #{v}
						@result.#{v}
					end
				}
			end
		end

		def word_search
			term_link = {}
			TERM_WSDL.values.each do |service|
				obj = SOAP::WSDLDriverFactory.new(service.wsdl).createDriver
				# obj.resetStream
				# obj.setWireDumpDev(File.open("/tmp/google_word.#{$$}", "w"))
				STDERR.puts "#{service.name} - creatDriver done."
				match = obj.doWordSearch( key ).exactMatchElements
				STDERR.puts "obj.doWordSearch done."
				unless match.empty? then
					STDERR.puts " #{service.name} - #{match.size} found!!"
					match.each do |node|
						wordlist = obj.getWordList(node.idref)
						wordlist.each do |word|
							term_link[service] = [] unless term_link[service]
							term_link[service] << {
								:name => word.name,
								:child => word.child,
								:parent => word.parent
							}
						end
					end
				end
			end
			term_link
		end

		def google_search
			google = SOAP::WSDLDriverFactory.new(GOOGLE_WSDL).createDriver
			STDERR.puts "Google - creatDriver done."
			google.resetStream
			google.setWireDumpDev(File.open("/tmp/google_cgi.#{$$}", "w"))
			result = google.doGoogleSearch( GOOGLE_KEY, key, page * MAX, MAX, false, "", false, "", 'utf-8', 'utf-8' )
			STDERR.puts "Google - doGoogleSearch done."
			result
		end

		def key
			@cgi['key'][0]
		end

		def page
			if @cgi.valid?( 'page' ) then
				@cgi['page'][0].to_i
			else
				0
			end
		end

		def first_page
			first = page - MAX_PAGE / 2
			if first< 0 then
				0
			else
				first
			end
		end

		def last_page
			last = @result.estimatedTotalResultsCount / MAX
			if last - first_page > MAX_PAGE then
				page + MAX_PAGE / 2
			else
				last
			end
		end

		def page_list ( base_url )
			result = ""
			unless first_page == 0 then
				result << "..."
			end
			( first_page .. last_page ).each do |i|
				if i == page
					result << "[#{i+1}]\n"
				else
					result << %Q[<a href="#{base_url};page=#{i}">[#{i+1}]</a>\n]
				end
			end
			unless last_page == 0 || last_page * MAX > estimatedTotalResultsCount then
				result << "..."
			end
			result
		end
	end
end
